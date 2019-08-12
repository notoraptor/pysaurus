import concurrent.futures
import os
from typing import Dict, Iterable, List, Optional, Set, Union

import ujson as json

from pysaurus.core import pysaurus_errors
from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.components.duration import Duration
from pysaurus.core.components.file_size import FileSize
from pysaurus.core.database import notifications, parallelism, path_utils
from pysaurus.core.database.video import Video
from pysaurus.core.notification import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.profiling import Profiler
from pysaurus.core.utils import functions as utils
from pysaurus.core.utils.constants import PYTHON_ERROR_NOTHING, THUMBNAIL_EXTENSION
from pysaurus.core.video_raptor.api import VideoRaptorResult


class Database(object):
    __slots__ = ['__database_path', '__json_path', '__folders', '__videos', '__unreadable',
                 '__system_is_case_insensitive', '__notifier', '__id_to_video', '__discarded']

    def __init__(self, path, folders=None, clear_old_folders=False, notifier=None):
        # type: (Union[AbsolutePath, str], Optional[Iterable[Union[AbsolutePath, str]]], Optional[bool], Optional[Notifier]) -> None
        path = AbsolutePath.ensure(path)
        if not path.isdir():
            raise pysaurus_errors.NotDirectoryError(path)
        self.__notifier = notifier or DEFAULT_NOTIFIER
        self.__database_path = path
        self.__json_path = AbsolutePath.new_file_path(self.__database_path, self.__database_path.title, 'json')
        self.__folders = set()  # type: Set[AbsolutePath]
        self.__videos = {}  # type: Dict[AbsolutePath, Video]
        self.__unreadable = {}  # type: Dict[AbsolutePath, List[str]]
        self.__system_is_case_insensitive = utils.file_system_is_case_insensitive(self.__database_path.path)
        self.__id_to_video = {}
        self.__discarded = {}
        self.__load(folders, clear_old_folders)
        self.__ensure_identifiers()
        self.save()

    def count_existing_videos(self):
        all_directories = {filename.get_directory() for filename in self.__videos}
        all_existing = set()
        for directory in all_directories:  # type: AbsolutePath
            if directory.isdir():
                for basename in directory.listdir():
                    if utils.is_valid_video_filename(basename):
                        all_existing.add(AbsolutePath.join(directory, basename))
        nb_not_found = 0
        nb_existing = 0
        for filename in self.__videos:
            if filename in all_existing:
                nb_existing += 1
            else:
                nb_not_found += 1
        return nb_not_found, nb_existing

    @property
    def nb_unreadable(self):
        return len(self.__unreadable)

    @property
    def nb_not_found(self):
        nb_not_found, _ = self.count_existing_videos()
        return nb_not_found

    @property
    def nb_valid(self):
        _, nb_valid = self.count_existing_videos()
        return nb_valid

    @property
    def nb_entries(self):
        return len(self.__videos) + self.nb_unreadable

    @property
    def nb_found(self):
        return self.nb_unreadable + self.nb_valid

    @property
    def nb_thumbnails(self):
        return sum((video.exists() and video.thumbnail_is_valid()) for video in self.__videos.values())

    @property
    def valid_size(self):
        return FileSize(sum(video.size for video in self.__videos.values() if video.exists()))

    @property
    def valid_length(self):
        return Duration(sum(video.get_duration().total_microseconds
                            for video in self.__videos.values() if video.exists()))

    @property
    def videos(self):
        return self.__videos.values()

    @property
    def valid_videos(self):
        return (video for video in self.__videos.values() if video.exists())

    @property
    def valid_videos_with_thumbnails(self):
        return (video for video in self.__videos.values() if video.exists() and video.thumbnail_is_valid())

    @property
    def folder(self):
        return self.__database_path

    def __load(self, folders=None, clear_old_folders=False):
        # type: (Optional[Iterable[Union[AbsolutePath, str]]], Optional[bool]) -> None

        if self.__json_path.exists():
            if not self.__json_path.isfile():
                raise pysaurus_errors.NotFileError(self.__json_path)
            with open(self.__json_path.path, 'r') as output_file:
                json_dict = json.load(output_file)
        else:
            json_dict = {}

        if not isinstance(json_dict, dict):
            raise pysaurus_errors.NotDirectoryError('Database file does not contain a dictionary.')
        # Parsing folders.
        if not clear_old_folders:
            for path in json_dict.get('folders', ()):
                self.__folders.add(AbsolutePath.ensure(path))
        if folders:
            for path in folders:
                self.__folders.add(AbsolutePath.ensure(path))
        # Parsing videos.
        for video_dict in json_dict.get('videos', ()):
            video = Video.from_dict(video_dict, self)
            if any(video.filename.in_directory(folder) for folder in self.__folders):
                self.__videos[video.filename] = video
            else:
                self.__discarded[video.filename] = video
        # Parsing unreadable.
        for d in json_dict.get('unreadable', ()):
            file_path = AbsolutePath(d['f'])
            errors = d['e']
            if file_path in self.__videos:
                # This should not happen. Anyway, remove this entry from database.
                # It may be recreated if database is updated.
                del self.__videos[file_path]
            self.__unreadable[file_path] = errors
        # Notify database loaded.
        self.__notify(notifications.DatabaseLoaded(self))

    def __ensure_identifiers(self):
        videos_without_identifiers = []
        for video in self.__videos.values():
            if video.video_id is None or video.video_id in self.__id_to_video:
                videos_without_identifiers.append(video)
            else:
                self.__id_to_video[video.video_id] = video
        next_id = (max(self.__id_to_video) + 1) if self.__id_to_video else 0
        for video in videos_without_identifiers:
            video.video_id = next_id
            next_id += 1
            self.__id_to_video[video.video_id] = video

    def save(self):
        # Save database.
        json_output = {
            'folders': [folder.path for folder in sorted(self.__folders)],
            'videos': [video.to_dict() for dct in (self.__videos, self.__discarded) for video in dct.values()],
            'unreadable': [{'f': file_name.path, 'e': errors} for file_name, errors in self.__unreadable.items()]
        }
        with open(self.__json_path.path, 'w') as output_file:
            json.dump(json_output, output_file)
        self.__notify(notifications.DatabaseSaved(self))

    def get_video_from_id(self, video_id):
        # type: (int) -> Optional[Video]
        return self.__id_to_video.get(video_id, None)

    def get_video_from_filename(self, filename):
        return self.__videos.get(AbsolutePath.ensure(filename), None)

    def update(self):
        cpu_count = os.cpu_count()
        video_errors = {}
        videos = {}
        all_file_names = []
        for file_name in self.get_videos_paths_from_disk():
            if file_name not in self.__videos and file_name not in self.__unreadable:
                all_file_names.append(file_name)
        self.__notify(notifications.VideosToLoad(len(all_file_names)))
        if not all_file_names:
            return

        jobs = utils.dispatch_tasks(all_file_names, cpu_count, extra_args=[self.__notifier])
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

        assert len(all_file_names) == len(videos) + len(video_errors)

        if videos:
            self.__videos.update(videos)
        if video_errors:
            self.__unreadable.update(video_errors)
            self.__notify(notifications.VideoInfoErrors(video_errors))
        if videos or video_errors:
            self.save()

    def ensure_thumbnails(self):
        cpu_count = os.cpu_count()
        valid_thumb_names = set()
        videos_without_thumbs = []
        thumb_to_videos = {}
        thumb_video_errors = {}
        thumb_jobs = []

        # Collect videos with and without thumbnails.
        existing_thumb_names = self.__get_thumbnails_names_on_disk()
        for video in self.__videos.values():
            if video.exists() and not video.error_thumbnail:
                thumb_name = video.ensure_thumbnail_name()
                if self.__system_is_case_insensitive:
                    thumb_name = thumb_name.lower()
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

        self.__notify(notifications.ThumbnailsToLoad(len(videos_without_thumbs)))
        if not videos_without_thumbs:
            self.__notify_missing_thumbnails()
            return

        for video in videos_without_thumbs:
            base_thumb_name = path_utils.generate_thumb_name(video.filename)
            thumb_name_index = 0
            thumb_name = base_thumb_name
            while thumb_name in valid_thumb_names:
                thumb_name = '%s_%d' % (base_thumb_name, thumb_name_index)
                thumb_name_index += 1
            video.thumb_name = thumb_name
            valid_thumb_names.add(thumb_name)
        self.save()

        dispatched_thumb_jobs = utils.dispatch_tasks(videos_without_thumbs, cpu_count)
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
                    if thumb_result.errors:
                        thumb_video_errors[file_name] = thumb_result.errors
                    else:
                        thumb_video_errors[file_name] = [PYTHON_ERROR_NOTHING]
                    self.__videos[AbsolutePath(file_name)].error_thumbnail = True
        assert nb_results == len(videos_without_thumbs)

        self.__notify_missing_thumbnails()
        if thumb_video_errors:
            self.__notify(notifications.VideoThumbnailErrors(thumb_video_errors))
        self.save()

    def clean_unused_thumbnails(self):
        existing_thumb_names = self.__get_thumbnails_names_on_disk()
        for video in self.__videos.values():
            if video.exists() and not video.error_thumbnail:
                thumb_name = video.ensure_thumbnail_name()
                if self.__system_is_case_insensitive:
                    thumb_name = thumb_name.lower()
                if thumb_name in existing_thumb_names:
                    existing_thumb_names.remove(thumb_name)
        self.__notify(notifications.UnusedThumbnails(len(existing_thumb_names)))
        for unused_thumb_name in existing_thumb_names:
            os.unlink(os.path.join(self.__database_path.path, '%s.%s' % (unused_thumb_name, THUMBNAIL_EXTENSION)))

    def remove_videos_not_found(self, save=False):
        videos_not_found = [video for video in self.__videos.values() if not video.exists()]
        if videos_not_found:
            for video in videos_not_found:
                self.delete_video(video)
            self.__notify(notifications.VideosNotFoundRemoved(len(videos_not_found)))
            if save:
                self.save()

    def delete_video(self, video):
        # type: (Video) -> None
        if video.filename.isfile():
            video.filename.delete()
        if video.filename in self.__videos:
            del self.__videos[video.filename]
            del self.__id_to_video[video.video_id]
        thumb_path = video.get_thumbnail_path()
        if thumb_path.isfile():
            thumb_path.delete()
        self.save()

    def change_video_file_title(self, video, new_title):
        # type: (Video, str) -> None
        if video.filename.title != new_title:
            new_filename = video.filename.new_title(new_title)
            if video.filename in self.__videos:
                del self.__videos[video.filename]
                self.__videos[new_filename] = video
                video.filename = new_filename
                self.save()

    def add_folder(self, folder):
        self.__folders.add(AbsolutePath.ensure(folder))

    def remove_folder(self, folder):
        folder = AbsolutePath.ensure(folder)
        if folder in self.__folders:
            self.__folders.remove(folder)

    def has_folder(self, folder):
        folder = AbsolutePath.ensure(folder)
        return folder in self.__folders

    def __get_thumbnails_names_on_disk(self):
        all_images_paths = []
        for path_string in self.__database_path.listdir():
            if path_string.lower().endswith('.%s' % THUMBNAIL_EXTENSION):
                if self.__system_is_case_insensitive:
                    path_string = path_string.lower()
                all_images_paths.append(path_string[:-(len(THUMBNAIL_EXTENSION) + 1)])
        return set(all_images_paths)

    def __notify_missing_thumbnails(self):
        remaining_thumb_videos = []
        existing_thumb_names = self.__get_thumbnails_names_on_disk()
        for video in self.__videos.values():
            if video.exists():
                missing = video.error_thumbnail
                if not missing:
                    thumb_name = video.ensure_thumbnail_name()
                    if self.__system_is_case_insensitive:
                        thumb_name = thumb_name.lower()
                    missing = thumb_name not in existing_thumb_names
                if missing:
                    remaining_thumb_videos.append(video.filename.path)
        self.__notify(notifications.MissingThumbnails(remaining_thumb_videos))

    def __notify(self, notification):
        self.__notifier.notify(notification)

    def get_videos_paths_from_disk(self):
        # type: () -> List[AbsolutePath]
        folder_to_files = {}
        cpu_count = os.cpu_count()
        jobs = utils.dispatch_tasks(sorted(self.__folders), cpu_count)
        paths = []  # type: List[AbsolutePath]
        with Profiler(title='Collect videos (%d threads)' % len(jobs), notifier=self.__notifier):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                results = list(executor.map(parallelism.job_collect_videos, jobs))
        for local_result in results:  # type: List[AbsolutePath]
            paths.extend(local_result)
        self.__notify(notifications.CollectedFiles(paths))
        return paths
