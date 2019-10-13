import concurrent.futures
import os
from typing import Dict, Iterable, List, Optional, Set, Union

import ujson as json

from pysaurus.core import exceptions, functions as utils
from pysaurus.core.components import AbsolutePath, DateModified, FilePath, PathType
from pysaurus.core.constants import PYTHON_ERROR_NOTHING, THUMBNAIL_EXTENSION
from pysaurus.core.database import notifications, parallelism
from pysaurus.core.database.video import Video
from pysaurus.core.database.video_state import VideoState
from pysaurus.core.modules import ImageUtils, System
from pysaurus.core.native.video_raptor.alignment import Miniature
from pysaurus.core.native.video_raptor.api import VideoRaptorResult
from pysaurus.core.notification import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.profiling import Profiler


class Database:
    __slots__ = ['__db_path', '__json_path', '__miniatures_path',
                 '__date', '__folders', '__videos', '__unreadable', '__discarded', '__disk',
                 '__notifier', '__id_to_video', 'system_is_case_insensitive']

    def __init__(self, path, folders=None, clear_old_folders=False, notifier=None):
        # type: (PathType, Optional[Iterable[PathType]], Optional[bool], Optional[Notifier]) -> None
        path = AbsolutePath.ensure(path)
        if not path.isdir():
            raise exceptions.NotDirectoryError(path)
        # Paths
        self.__db_path = path
        self.__json_path = FilePath(self.__db_path, self.__db_path.title, 'json')
        self.__miniatures_path = FilePath(self.__db_path, '%s.miniatures' % self.__db_path.title, 'json')
        # Database data
        self.__date = DateModified.now()
        self.__folders = set()  # type: Set[AbsolutePath]
        self.__videos = {}  # type: Dict[AbsolutePath, Video]
        self.__unreadable = {}  # type: Dict[AbsolutePath, VideoState]
        self.__discarded = {}  # type: Dict[AbsolutePath, VideoState]
        # RAM data
        self.__disk = set()  # type: Set[AbsolutePath]
        self.__notifier = notifier or DEFAULT_NOTIFIER
        self.__id_to_video = {}  # type: Dict[int, Union[VideoState, Video]]
        self.system_is_case_insensitive = System.is_case_insensitive(self.__db_path.path)
        # Load database
        self.__load(folders, clear_old_folders)
        self.save()

    # Properties.

    folder = property(lambda self: self.__db_path)
    nb_entries = property(lambda self: len(self.__videos) + len(self.__unreadable) + len(self.__discarded))
    nb_discarded = property(lambda self: len(self.__discarded))
    nb_unreadable = property(lambda self: len(self.__unreadable))
    nb_not_found = property(lambda self: sum(1 for _ in self.videos(unreadable=True, found=False, not_found=True)))
    nb_found = property(lambda self: sum(1 for _ in self.videos(valid=True, unreadable=True)))
    nb_valid = property(lambda self: sum(1 for _ in self.videos()))
    nb_thumbnails = property(lambda self: sum(1 for _ in self.videos(no_thumbs=False)))

    # Private utility methods.

    def __filter_not_found(self, video):
        return not self.video_exists(video.filename)

    def __filter_found(self, video):
        return self.video_exists(video.filename)

    def __filter_no_thumbs(self, video):
        return not video.thumbnail_is_valid()

    def __filter_with_thumbs(self, video):
        return video.thumbnail_is_valid()

    def __in_folders(self, path):
        # type: (AbsolutePath) -> bool
        return any(path.in_directory(folder) for folder in self.__folders)

    def __get_thumbnails_names_on_disk(self):
        # type: () -> Set[str]
        all_images_paths = set()
        for path_string in self.__db_path.listdir():
            if path_string.lower().endswith('.%s' % THUMBNAIL_EXTENSION):
                if self.system_is_case_insensitive:
                    path_string = path_string.lower()
                all_images_paths.add(path_string[:-(len(THUMBNAIL_EXTENSION) + 1)])
        return all_images_paths

    def __notify_missing_thumbnails(self):
        remaining_thumb_videos = []
        existing_thumb_names = self.__get_thumbnails_names_on_disk()
        for video in self.__videos.values():
            if (isinstance(video, Video) and video.filename.isfile()
                    and (video.error_thumbnail or video.ensure_thumbnail_name() not in existing_thumb_names)):
                remaining_thumb_videos.append(video.filename.path)
        self.__notifier.notify(notifications.MissingThumbnails(remaining_thumb_videos))

    # Private methods.

    def __load(self, folders=None, clear_old_folders=False):
        # type: (Optional[Iterable[PathType]], Optional[bool]) -> None

        if self.__json_path.exists():
            if not self.__json_path.isfile():
                raise exceptions.NotFileError(self.__json_path)
            with open(self.__json_path.path, 'r') as output_file:
                json_dict = json.load(output_file)
            if not isinstance(json_dict, dict):
                raise exceptions.PysaurusError('Database file does not contain a dictionary.')
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
            if video_dict['U']:
                video_state = VideoState.from_dict(video_dict, self)
                destination = self.__unreadable
            else:
                video_state = Video.from_dict(video_dict, self)
                destination = self.__videos
            if self.__in_folders(video_state.filename):
                destination[video_state.filename] = video_state
            else:
                self.__discarded[video_state.filename] = video_state

    def __ensure_identifiers(self):
        without_identifiers = []
        for source in (self.__videos, self.__unreadable):
            for video_state in source.values():
                if not isinstance(video_state.video_id, int) or video_state.video_id in self.__id_to_video:
                    without_identifiers.append(video_state)
                else:
                    self.__id_to_video[video_state.video_id] = video_state
        next_id = (max(self.__id_to_video) + 1) if self.__id_to_video else 0
        for video_state in without_identifiers:
            video_state.video_id = next_id
            next_id += 1
            self.__id_to_video[video_state.video_id] = video_state

    # Public methods.

    def videos(self, valid=True, unreadable=False, found=True, not_found=False, with_thumbs=True, no_thumbs=True):

        if found is not_found is with_thumbs is no_thumbs is False:
            return ()

        sources = []
        filters = []

        if valid:
            sources.append(self.__videos)
        if unreadable:
            sources.append(self.__unreadable)

        if not found and not_found:
            filters.append(self.__filter_not_found)
        elif found and not not_found:
            filters.append(self.__filter_found)

        if not with_thumbs and no_thumbs:
            filters.append(self.__filter_no_thumbs)
        elif with_thumbs and not no_thumbs:
            filters.append(self.__filter_with_thumbs)

        return (video for dictionary in sources for video in dictionary.values() if all(fn(video) for fn in filters))

    def save(self):
        self.__ensure_identifiers()
        # Save database.
        json_output = {'date': self.__date.time,
                       'folders': [folder.path for folder in self.__folders],
                       'videos': [video.to_dict()
                                  for dct in (self.__videos, self.__unreadable, self.__discarded)
                                  for video in dct.values()]}
        json_output['folders'].sort()
        json_output['videos'].sort(key=lambda dct: dct['f'])
        with open(self.__json_path.path, 'w') as output_file:
            json.dump(json_output, output_file)
        self.__notifier.notify(notifications.DatabaseSaved(self))

    def update(self):
        cpu_count = os.cpu_count()
        videos = {}
        unreadable = {}
        all_file_names = []

        file_names = self.check_videos_on_disk()
        current_date = DateModified.now()

        self.__notifier.notify(notifications.DatabaseReady(self))

        for file_name in file_names:  # type: AbsolutePath
            video_state = None
            if file_name in self.__videos:
                video_state = self.__videos[file_name]
            elif file_name in self.__unreadable:
                video_state = self.__unreadable[file_name]
            if (not video_state
                    or file_name.get_date_modified() >= self.__date
                    or file_name.get_size() != video_state.file_size):
                all_file_names.append(file_name.path)

        nb_to_load = len(all_file_names)

        self.__notifier.notify(notifications.VideosToLoad(nb_to_load))
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
                else:
                    unreadable[file_path] = VideoState(filename=file_path,
                                                       size=file_path.get_size(),
                                                       errors=(result.errors or [PYTHON_ERROR_NOTHING]),
                                                       database=self)

        del results
        assert nb_to_load == len(videos) + len(unreadable)

        if videos:
            self.__videos.update(videos)
        if unreadable:
            self.__unreadable.update(unreadable)
            self.__notifier.notify(notifications.VideoInfoErrors(unreadable))
        if videos or unreadable:
            self.__date = current_date
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
            if self.video_exists(video.filename) and not video.error_thumbnail:
                thumb_name = video.ensure_thumbnail_name()
                if thumb_name in existing_thumb_names:
                    thumb_to_videos.setdefault(thumb_name, []).append(video)
                else:
                    videos_without_thumbs.append(video)

        # If a thumbnail name is associated to many videos,
        # consider these videos don't have thumbnails.
        for valid_thumb_name, vds in thumb_to_videos.items():
            if len(vds) == 1:
                valid_thumb_names.add(valid_thumb_name)
            else:
                videos_without_thumbs.extend(vds)
        nb_videos_no_thumbs = len(videos_without_thumbs)
        del thumb_to_videos

        self.__notifier.notify(notifications.ThumbnailsToLoad(nb_videos_no_thumbs))
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
            thumb_jobs.append((job_file_names, job_thumb_names, self.__db_path.path, job_id, self.__notifier))
        with Profiler(title='Get thumbnails through %d thread(s)' % len(thumb_jobs), notifier=self.__notifier):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                thumb_results = list(executor.map(parallelism.job_videos_thumbnails, thumb_jobs))

        nb_results = 0
        for local_file_names, local_thumb_results in thumb_results:  # type: dict
            nb_results += len(local_file_names)
            for file_name, thumb_result in zip(local_file_names, local_thumb_results):  # type: (str, VideoRaptorResult)
                if not thumb_result.done:
                    thumb_errors[file_name] = thumb_result.errors or [PYTHON_ERROR_NOTHING]
                    self.__videos[AbsolutePath(file_name)].error_thumbnail = True
        del thumb_results
        assert nb_results == nb_videos_no_thumbs

        self.__notify_missing_thumbnails()
        if thumb_errors:
            self.__notifier.notify(notifications.VideoThumbnailErrors(thumb_errors))
        self.save()

    def ensure_miniatures(self):
        # type: () -> Dict[str, Miniature]
        miniatures = {}
        if self.__miniatures_path.exists():
            if not self.__miniatures_path.isfile():
                raise exceptions.NotFileError(self.__miniatures_path)
            with open(self.__miniatures_path.path, 'r') as miniatures_file:
                json_dict = json.load(miniatures_file)
            if not isinstance(json_dict, list):
                raise exceptions.PysaurusError('Miniatures file does not contain a list.')
            for dct in json_dict:
                video = self.get_video_from_filename(AbsolutePath.ensure(dct['i']))
                if video and video.filename.isfile() and ImageUtils.DEFAULT_THUMBNAIL_SIZE == (dct['w'], dct['h']):
                    miniature = Miniature.from_dict(dct)
                    miniatures[miniature.identifier] = miniature
            del json_dict
        tasks = [(video.filename, video.get_thumbnail_path())
                 for video in self.videos(no_thumbs=False)
                 if video.filename.path not in miniatures]
        print('Missing', len(tasks), '/', len(tasks) + len(miniatures), 'miniature(s).')
        if not tasks:
            return miniatures
        cpu_count = os.cpu_count()
        jobs = utils.dispatch_tasks(tasks, cpu_count)
        del tasks
        with Profiler('Generating miniatures.'):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                results = list(executor.map(parallelism.job_generate_miniatures, jobs))
        del jobs
        for local_array in results:
            for miniature in local_array:  # type: Miniature
                miniature.identifier = miniature.identifier.path
                miniatures[miniature.identifier] = miniature
        del results
        with open(self.__miniatures_path.path, 'w') as output_file:
            json.dump([miniatures[identifier].to_dict() for identifier in sorted(miniatures)], output_file)
        return miniatures

    # Public features.

    def check_videos_on_disk(self, use_list_dir=False):
        # type: (bool) -> Set[AbsolutePath]
        cpu_count = os.cpu_count()
        jobs = utils.dispatch_tasks(sorted(self.__folders), cpu_count)
        with Profiler(title='Collect videos using %s (%d threads)' %
                            ('listdir' if use_list_dir else 'walk', len(jobs)),
                      notifier=self.__notifier):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                results = list(executor.map(parallelism.job_collect_videos_listdir
                                            if use_list_dir else parallelism.job_collect_videos_walk,
                                            jobs))
        self.__disk.clear()
        for local_result in results:  # type: List[AbsolutePath]
            self.__disk.update(local_result)
        self.__notifier.notify(notifications.FinishedCollectingVideos(self.__disk))
        return self.__disk

    def video_exists(self, path):
        return path in self.__disk

    def get_video_from_id(self, video_id, required=False, accept_unreadable=False):
        # type: (int, bool, bool) -> Optional[Video]
        if video_id in self.__id_to_video and (accept_unreadable or isinstance(self.__id_to_video[video_id], Video)):
            return self.__id_to_video[video_id]
        if required:
            raise exceptions.UnknownVideoID(video_id)
        return None

    def get_video_from_filename(self, filename, required=False, accept_unreadable=False):
        # type: (PathType, bool, bool) -> Optional[Video]
        filename = AbsolutePath.ensure(filename)
        if filename in self.__videos and (accept_unreadable or isinstance(self.__videos[filename], Video)):
            return self.__videos[filename]
        if required:
            raise exceptions.UnknownVideoFilename(filename)
        return None

    def remove_videos_not_found(self):
        nb_removed = 0
        for video in list(self.__videos.values()):
            if not video.filename.isfile():
                self.delete_video(video)
                nb_removed += 1
        if nb_removed:
            self.__notifier.notify(notifications.VideosNotFoundRemoved(nb_removed))
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
            video.get_thumbnail_path().delete()
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

    # Unused.

    def clean_unused_thumbnails(self):
        existing_thumb_names = self.__get_thumbnails_names_on_disk()
        for video in self.__videos.values():
            if isinstance(video, Video) and video.filename.isfile() and not video.error_thumbnail:
                thumb_name = video.ensure_thumbnail_name()
                if thumb_name in existing_thumb_names:
                    existing_thumb_names.remove(thumb_name)
        self.__notifier.notify(notifications.UnusedThumbnails(len(existing_thumb_names)))
        for unused_thumb_name in existing_thumb_names:
            AbsolutePath.join(
                self.__db_path.path, '%s.%s' % (unused_thumb_name, THUMBNAIL_EXTENSION)).delete()
