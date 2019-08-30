import concurrent.futures
import os
from typing import Dict, Iterable, List, Optional, Set, Union

import ujson as json

from pysaurus.core import pysaurus_errors
from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.components.date_modified import DateModified
from pysaurus.core.components.duration import Duration
from pysaurus.core.components.file_size import FileSize
from pysaurus.core.database import notifications, parallelism
from pysaurus.core.database.video import Video
from pysaurus.core.database.video_state import VideoState
from pysaurus.core.notification import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.profiling import Profiler
from pysaurus.core.utils import functions as utils
from pysaurus.core.utils.constants import PYTHON_ERROR_NOTHING, THUMBNAIL_EXTENSION
from pysaurus.core.video_raptor.api import VideoRaptorResult

Path = Union[AbsolutePath, str]


class Database(object):
    __slots__ = ['__database_path', '__json_path', '__date', '__folders', '__videos', '__discarded',
                 '__notifier', '__id_to_video', 'system_is_case_insensitive']

    def __init__(self, path, folders=None, clear_old_folders=False, notifier=None):
        # type: (Path, Optional[Iterable[Path]], Optional[bool], Optional[Notifier]) -> None
        path = AbsolutePath.ensure(path)
        if not path.isdir():
            raise pysaurus_errors.NotDirectoryError(path)
        # Database folder path
        self.__database_path = path
        # JSON file path
        self.__json_path = AbsolutePath.new_file_path(self.__database_path, self.__database_path.title, 'json')
        # Database data
        self.__date = DateModified.now()
        self.__folders = set()  # type: Set[AbsolutePath]
        self.__videos = {}  # type: Dict[AbsolutePath, Union[VideoState, Video]]
        self.__discarded = {}  # type: Dict[AbsolutePath, VideoState]
        # RAM data
        self.__id_to_video = {}  # type: Dict[int, Union[VideoState, Video]]
        self.system_is_case_insensitive = utils.file_system_is_case_insensitive(self.__database_path.path)
        self.__notifier = notifier or DEFAULT_NOTIFIER
        # Load database
        self.__load(folders, clear_old_folders)
        self.__ensure_identifiers()
        self.save()

    # Properties.

    @property
    def folder(self):
        return self.__database_path

    @property
    def nb_entries(self):
        return len(self.__videos) + len(self.__discarded)

    @property
    def nb_discarded(self):
        return len(self.__discarded)

    @property
    def nb_not_found(self):
        return sum(not filename.isfile() for filename in self.__videos)

    @property
    def nb_found(self):
        return sum(filename.isfile() for filename in self.__videos)

    @property
    def nb_unreadable(self):
        return sum(video.filename.isfile() and video.unreadable for video in self.__videos.values())

    @property
    def nb_valid(self):
        return sum(video.filename.isfile() and not video.unreadable for video in self.__videos.values())

    @property
    def nb_thumbnails(self):
        return sum(isinstance(video, Video) and video.filename.isfile() and video.thumbnail_is_valid()
                   for video in self.__videos.values())

    @property
    def valid_size(self):
        return FileSize(sum(video.size for video in self.__videos.values()
                            if isinstance(video, Video) and video.filename.isfile()))

    @property
    def valid_length(self):
        return Duration(sum(video.get_duration().total_microseconds for video in self.__videos.values()
                            if isinstance(video, Video) and video.filename.isfile()))

    @property
    def videos_not_found(self):
        return (video for video in self.__videos.values() if not video.filename.isfile())

    @property
    def unreadable_videos(self):
        return (video for video in self.__videos.values() if video.filename.isfile() and video.unreadable)

    @property
    def valid_videos(self):
        # type: () -> Iterable[Video]
        return (video for video in self.__videos.values() if video.filename.isfile() and not video.unreadable)

    @property
    def valid_videos_with_thumbnails(self):
        return (video for video in self.__videos.values()
                if isinstance(video, Video) and video.filename.isfile() and video.thumbnail_is_valid())

    # Private utility methods.

    def __in_folders(self, path):
        # type: (AbsolutePath) -> bool
        return any(path.in_directory(folder) for folder in self.__folders)

    def __get_thumbnails_names_on_disk(self):
        all_images_paths = []
        for path_string in self.__database_path.listdir():
            if path_string.lower().endswith('.%s' % THUMBNAIL_EXTENSION):
                if self.system_is_case_insensitive:
                    path_string = path_string.lower()
                all_images_paths.append(path_string[:-(len(THUMBNAIL_EXTENSION) + 1)])
        return set(all_images_paths)

    def __get_videos_paths_from_disk(self):
        # type: () -> List[AbsolutePath]
        cpu_count = os.cpu_count()
        jobs = utils.dispatch_tasks(sorted(self.__folders), cpu_count)
        paths = []  # type: List[AbsolutePath]
        with Profiler(title='Collect videos (%d threads)' % len(jobs), notifier=self.__notifier):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                results = list(executor.map(parallelism.job_collect_videos, jobs))
        for local_result in results:  # type: List[AbsolutePath]
            paths.extend(local_result)
        self.__notify(notifications.FinishedCollectingVideos(paths))
        return paths

    def __notify_missing_thumbnails(self):
        remaining_thumb_videos = []
        existing_thumb_names = self.__get_thumbnails_names_on_disk()
        for video in self.__videos.values():
            if (isinstance(video, Video) and video.filename.isfile()
                    and (video.error_thumbnail or video.ensure_thumbnail_name() not in existing_thumb_names)):
                remaining_thumb_videos.append(video.filename.path)
        self.__notify(notifications.MissingThumbnails(remaining_thumb_videos))

    def __notify(self, notification):
        self.__notifier.notify(notification)

    # Private methods.

    def __load(self, folders=None, clear_old_folders=False):
        # type: (Optional[Iterable[Path]], Optional[bool]) -> None

        if self.__json_path.exists():
            if not self.__json_path.isfile():
                raise pysaurus_errors.NotFileError(self.__json_path)
            with open(self.__json_path.path, 'r') as output_file:
                json_dict = json.load(output_file)
            if not isinstance(json_dict, dict):
                raise pysaurus_errors.NotDirectoryError('Database file does not contain a dictionary.')
        else:
            json_dict = {}

        # Parsing date.
        if 'date' in json_dict:
            self.__date = DateModified(json_dict['date'])
        # Parsing folders.
        if not clear_old_folders:
            for path in json_dict.get('folders', ()):
                self.__folders.add(AbsolutePath.ensure(path))
        if folders:
            for path in folders:
                self.__folders.add(AbsolutePath.ensure(path))
        # Parsing videos.
        for video_dict in json_dict.get('videos', ()):
            if 'U' in video_dict:
                assert video_dict['U']
                video_state = VideoState.from_dict(video_dict, self)
            else:
                video_state = Video.from_dict(video_dict, self)
            if self.__in_folders(video_state.filename):
                self.__videos[video_state.filename] = video_state
            else:
                self.__discarded[video_state.filename] = video_state

        # Notify database loaded.
        self.__notify(notifications.DatabaseLoaded(self))

    def __ensure_identifiers(self):
        without_identifiers = []
        for video_state in self.__videos.values():
            if video_state.video_id is None or video_state.video_id in self.__id_to_video:
                without_identifiers.append(video_state)
            else:
                self.__id_to_video[video_state.video_id] = video_state
        next_id = (max(self.__id_to_video) + 1) if self.__id_to_video else 0
        for video_state in without_identifiers:
            video_state.video_id = next_id
            next_id += 1
            self.__id_to_video[video_state.video_id] = video_state

    # Public methods.

    def save(self):
        # Save database.
        json_output = {'folders': [folder.path for folder in self.__folders],
                       'videos': [video.to_dict()
                                  for dct in (self.__videos, self.__discarded)
                                  for video in dct.values()]}
        json_output['folders'].sort()
        json_output['videos'].sort(key=lambda dct: dct['f'])
        with open(self.__json_path.path, 'w') as output_file:
            json.dump(json_output, output_file)
        self.__notify(notifications.DatabaseSaved(self))

    def update(self):
        cpu_count = os.cpu_count()
        video_errors = {}
        videos = {}
        all_file_names = []

        for file_name in self.__get_videos_paths_from_disk():  # type: AbsolutePath
            if (file_name not in self.__videos
                    or file_name.get_date_modified() >= self.__date
                    or file_name.get_size() != self.__videos[file_name].size):
                all_file_names.append(file_name.path)

        nb_to_load = len(all_file_names)

        self.__notify(notifications.VideosToLoad(nb_to_load))
        if not all_file_names:
            return

        jobs = utils.dispatch_tasks(all_file_names, cpu_count, extra_args=[self.__notifier])
        del all_file_names

        with Profiler(title='Get videos info (%d threads)' % len(jobs), notifier=self.__notifier):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                results = list(executor.map(parallelism.job_videos_info, jobs))

        for (local_file_names, local_results) in results:  # type: dict
            for file_name, result in zip(local_file_names, local_results):  # type: (str, VideoRaptorResult)
                file_path = AbsolutePath.ensure(file_name)
                if result.done:  # type: Video
                    videos[file_path] = Video(database=self, **result.done)
                elif result.errors:
                    video_errors[file_path] = result.errors
                else:
                    video_errors[file_path] = [PYTHON_ERROR_NOTHING]

        del results
        assert nb_to_load == len(videos) + len(video_errors)

        if videos:
            self.__videos.update(videos)
        if video_errors:
            for file_name, errors in video_errors.items():
                self.__videos[file_name] = VideoState(file_name, file_name.get_size(), True, errors, None)
            self.__notify(notifications.VideoInfoErrors(video_errors))
        if videos or video_errors:
            self.save()

    def ensure_thumbnails(self):
        cpu_count = os.cpu_count()
        valid_thumb_names = set()
        videos_without_thumbs = []
        thumb_to_videos = {}
        thumb_errors = {}
        thumb_jobs = []

        # Collect videos with and without thumbnails.
        existing_thumb_names = self.__get_thumbnails_names_on_disk()
        for video in self.__videos.values():
            if isinstance(video, Video) and video.filename.isfile() and not video.error_thumbnail:
                thumb_name = video.ensure_thumbnail_name()
                if thumb_name in existing_thumb_names:
                    thumb_to_videos.setdefault(thumb_name, []).append(video)
                else:
                    videos_without_thumbs.append(video)

        # If a thumbnail name is associated to many videos, consider these videos don't have thumbnails.
        for valid_thumb_name, vds in thumb_to_videos.items():
            if len(vds) == 1:
                valid_thumb_names.add(valid_thumb_name)
            else:
                videos_without_thumbs.extend(vds)
        nb_videos_no_thumbs = len(videos_without_thumbs)
        del thumb_to_videos

        self.__notify(notifications.ThumbnailsToLoad(nb_videos_no_thumbs))
        if not videos_without_thumbs:
            self.__notify_missing_thumbnails()
            return

        for video in videos_without_thumbs:
            base_thumb_name = video.ensure_thumbnail_name()
            thumb_name_index = 0
            thumb_name = base_thumb_name
            while thumb_name in valid_thumb_names:
                thumb_name = '%s_%d' % (base_thumb_name, thumb_name_index)
                thumb_name_index += 1
            video.thumb_name = thumb_name
            valid_thumb_names.add(thumb_name)
        del valid_thumb_names
        self.save()

        dispatched_thumb_jobs = utils.dispatch_tasks(videos_without_thumbs, cpu_count)
        del videos_without_thumbs
        for job_videos, job_id in dispatched_thumb_jobs:
            job_file_names = []
            job_thumb_names = []
            for video in job_videos:
                job_file_names.append(video.filename.path)
                job_thumb_names.append(video.thumb_name)
            thumb_jobs.append((job_file_names, job_thumb_names, self.__database_path.path, job_id, self.__notifier))
        with Profiler(title='Get thumbnails through %d thread(s)' % len(thumb_jobs), notifier=self.__notifier):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                thumb_results = list(executor.map(parallelism.job_videos_thumbnails, thumb_jobs))

        nb_results = 0
        for (local_file_names, local_thumb_results) in thumb_results:  # type: dict
            nb_results += len(local_file_names)
            for file_name, thumb_result in zip(local_file_names, local_thumb_results):  # type: (str, VideoRaptorResult)
                if not thumb_result.done:
                    thumb_errors[file_name] = thumb_result.errors if thumb_result.errors else [PYTHON_ERROR_NOTHING]
                    self.__videos[AbsolutePath(file_name)].error_thumbnail = True
        del thumb_results
        assert nb_results == nb_videos_no_thumbs

        self.__notify_missing_thumbnails()
        if thumb_errors:
            self.__notify(notifications.VideoThumbnailErrors(thumb_errors))
        self.save()

    # Public features.

    def get_video_from_id(self, video_id, required=False, accept_unreadable=False):
        # type: (int, bool, bool) -> Optional[Video]
        if video_id in self.__id_to_video and (accept_unreadable or isinstance(self.__id_to_video[video_id], Video)):
            return self.__id_to_video[video_id]
        if required:
            raise pysaurus_errors.UnknownVideoID(video_id)
        return None

    def get_video_from_filename(self, filename, required=False, accept_unreadable=False):
        # type: (Path, bool, bool) -> Optional[Video]
        filename = AbsolutePath.ensure(filename)
        if filename in self.__videos and (accept_unreadable or isinstance(self.__videos[filename], Video)):
            return self.__videos[filename]
        if required:
            raise pysaurus_errors.UnknownVideoFilename(filename)
        return None

    def clean_unused_thumbnails(self):
        existing_thumb_names = self.__get_thumbnails_names_on_disk()
        for video in self.__videos.values():
            if isinstance(video, Video) and video.filename.isfile() and not video.error_thumbnail:
                thumb_name = video.ensure_thumbnail_name()
                if thumb_name in existing_thumb_names:
                    existing_thumb_names.remove(thumb_name)
        self.__notify(notifications.UnusedThumbnails(len(existing_thumb_names)))
        for unused_thumb_name in existing_thumb_names:
            os.unlink(os.path.join(self.__database_path.path, '%s.%s' % (unused_thumb_name, THUMBNAIL_EXTENSION)))

    def remove_videos_not_found(self, save=False):
        nb_removed = 0
        for video in list(self.__videos.values()):
            if not video.filename.isfile():
                self.delete_video(video)
                nb_removed += 1
        if nb_removed:
            self.__notify(notifications.VideosNotFoundRemoved(nb_removed))
            if save:
                self.save()

    def delete_video(self, video):
        # type: (VideoState) -> AbsolutePath
        if video.filename.isfile():
            video.filename.delete()
        if video.filename in self.__videos:
            del self.__videos[video.filename]
            if isinstance(video, Video):
                del self.__id_to_video[video.video_id]
        if isinstance(video, Video):
            thumb_path = video.get_thumbnail_path()
            if thumb_path.isfile():
                thumb_path.delete()
        self.save()
        return video.filename

    def change_video_file_title(self, video, new_title):
        # type: (Video, str) -> None
        if video.filename.title != new_title:
            new_filename = video.filename.new_title(new_title)
            if video.filename in self.__videos:
                del self.__videos[video.filename]
                self.__videos[new_filename] = video
                video.filename = new_filename
                self.save()
