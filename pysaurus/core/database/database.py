import concurrent.futures
import os
from typing import Dict, List, Optional, Set, Union

import ujson as json

from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.components.duration import Duration
from pysaurus.core.components.file_size import FileSize
from pysaurus.core.database import notifications, path_utils, parallelism
from pysaurus.core.database.video import Video
from pysaurus.core.notification import Notifier, DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler
from pysaurus.core.utils import functions as utils
from pysaurus.core.utils.constants import PYTHON_ERROR_NOTHING, THUMBNAIL_EXTENSION
from pysaurus.core.video_raptor.api import VideoRaptorResult


class Database(object):
    __slots__ = ['__list_path', '__json_path', '__database_path', '__folders', '__videos', '__unreadable',
                 '__id_to_file_name', '__file_name_to_id', '__system_is_case_insensitive', '__notifier']

    def __init__(self, list_file_path, notifier=None):
        # type: (Union[AbsolutePath, str], Optional[Notifier]) -> None
        self.__notifier = notifier or DEFAULT_NOTIFIER
        self.__list_path = AbsolutePath.ensure(list_file_path)
        self.__database_path = self.__list_path.get_directory()
        self.__json_path = AbsolutePath.new_file_path(self.__database_path, self.__list_path.title, 'json')
        self.__folders = path_utils.load_path_list_file(self.__list_path)
        self.__videos = {}  # type: Dict[AbsolutePath, Video]
        self.__id_to_file_name = {}  # type: Dict[int, AbsolutePath]
        self.__file_name_to_id = {}  # type: Dict[AbsolutePath, int]
        self.__unreadable = {}  # type: Dict[AbsolutePath, List[str]]
        self.__system_is_case_insensitive = utils.file_system_is_case_insensitive(self.__database_path.path)
        self.load()

    def videos_by_folder(self):
        common_path_to_videos = {}  # type: Dict[str, List[Video]]
        for video in self.__videos.values():
            if common_path_to_videos:
                previous_path = ''
                common_prefix = ''
                for path_string in common_path_to_videos:
                    common_prefix = utils.longest_common_path(path_string, video.filename.standard_path)
                    if common_prefix:
                        previous_path = path_string
                        break
                if common_prefix:
                    videos = common_path_to_videos.pop(previous_path)
                    videos.append(video)
                    common_path_to_videos[common_prefix] = videos
                    continue
            common_path_to_videos[video.filename.standard_path] = [video]
        folder_to_videos = {}
        for common_path, videos in common_path_to_videos.items():
            absolute_path = AbsolutePath(common_path)
            assert absolute_path.isdir(), common_path
            folder_to_videos[absolute_path] = videos
        return folder_to_videos

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
        return sum((not video.error_thumbnail and video.thumbnail_is_valid(self.__database_path))
                   for video in self.__videos.values())

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

    def get_video_from_id(self, video_id):
        # type: (int) -> Optional[Video]
        if video_id in self.__id_to_file_name:
            return self.__videos[self.__id_to_file_name[video_id]]
        return None

    def get_video_id(self, video):
        # type: (Video) -> Optional[int]
        return self.__file_name_to_id.get(video.filename, None)

    def update(self):
        folder_to_files = self.get_videos_paths_from_disk()
        cpu_count = os.cpu_count()
        video_errors = {}
        videos = {}
        all_file_names = [file_name.path
                          for file_names in folder_to_files.values()
                          for file_name in file_names
                          if file_name not in self.__videos and file_name not in self.__unreadable]
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
                    if result.errors:
                        result.done.errors.update(result.errors)
                    videos[file_path] = result.done
                elif result.errors:
                    video_errors[file_path] = result.errors
                else:
                    video_errors[file_path] = [PYTHON_ERROR_NOTHING]

        assert len(all_file_names) == len(videos) + len(video_errors)
        self.__notify(notifications.VideosLoaded(len(videos)))

        # Parsing messages.
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
        self.save(update_identifiers=False)

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
        self.save(update_identifiers=False)

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
            del self.__id_to_file_name[self.__file_name_to_id.pop(video.filename)]
        thumb_path = video.get_thumbnail_path(self.__database_path)
        if thumb_path.isfile():
            thumb_path.delete()

    def change_video_file_title(self, video, new_title):
        # type: (Video, str) -> None
        if video.filename.title != new_title:
            new_filename = video.filename.new_title(new_title)
            if video.filename in self.__videos:
                del self.__videos[video.filename]
                self.__videos[new_filename] = video
                video.filename = new_filename
                self.save(update_identifiers=True)

    def add_folder(self, folder):
        self.__folders.add(AbsolutePath.ensure(folder))

    def remove_folder(self, folder):
        folder = AbsolutePath.ensure(folder)
        if folder in self.__folders:
            self.__folders.remove(folder)

    def has_folder(self, folder):
        folder = AbsolutePath.ensure(folder)
        return folder in self.__folders

    def load(self):
        if self.__json_path.isfile():
            with open(self.__json_path.path, 'r') as output_file:
                json_dict = json.load(output_file)
            if isinstance(json_dict, list):
                json_dict = {
                    'videos': json_dict,
                    'unreadable': []
                }
            self.__videos = {video.filename: video for video in (Video.from_dict(dct) for dct in json_dict['videos'])
                             if any(video.filename.in_directory(folder) for folder in self.__folders)}
            for d in json_dict['unreadable']:
                file_path = AbsolutePath(d['f'])
                errors = d['e']
                if file_path in self.__videos:
                    # This should not happen. Anyway, remove this entry from database.
                    # It may be recreated if database is updated.
                    del self.__videos[file_path]
                elif file_path.isfile():
                    # Keep errors only for existing files.
                    self.__unreadable[file_path] = errors
        # Generate videos identifiers.
        self.__generate_identifiers()
        # Notify database loaded.
        self.__notify(notifications.DatabaseLoaded(self))

    def save(self, update_identifiers=True):
        if update_identifiers:
            # Regenerate runtime ids.
            self.__generate_identifiers()
        # Ensure database folder.
        self.__database_path.mkdir()
        # Save list file.
        with open(self.__list_path.path, 'w') as list_file:
            for folder in sorted(self.__folders):
                list_file.writelines(folder.path)
                list_file.writelines('\n')
        # Save videos entries.
        with open(self.__json_path.path, 'w') as output_file:
            json_output = {
                'videos': [video.to_dict() for video in self.__videos.values()],
                'unreadable': [{'f': str(file_name), 'e': errors}
                               for file_name, errors in self.__unreadable.items()]
            }
            json.dump(json_output, output_file, indent=1)
            self.__notify(notifications.DatabaseSaved(self))

    def __get_thumbnails_names_on_disk(self):
        all_images_paths = []
        for path_string in self.__database_path.listdir():
            if path_string.lower().endswith('.%s' % THUMBNAIL_EXTENSION):
                if self.__system_is_case_insensitive:
                    path_string = path_string.lower()
                all_images_paths.append(path_string[:-(len(THUMBNAIL_EXTENSION) + 1)])
        return set(all_images_paths)

    def __generate_identifiers(self):
        self.__id_to_file_name = {index: filename for index, filename in enumerate(sorted(self.__videos))}
        self.__file_name_to_id = {filename: index for index, filename in self.__id_to_file_name.items()}

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
        # type: () -> Dict[AbsolutePath, Set[AbsolutePath]]
        folder_to_files = {}
        cpu_count = os.cpu_count()
        jobs = utils.dispatch_tasks(sorted(self.__folders), cpu_count, extra_args=[self.__notifier])
        with Profiler(title='Collect videos (%d threads)' % len(jobs), notifier=self.__notifier):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                results = list(executor.map(parallelism.job_collect_videos, jobs))
        for local_result in results:  # type: Dict[AbsolutePath, Set[AbsolutePath]]
            for folder, files in local_result.items():
                folder_to_files.setdefault(folder, set()).update(files)
        self.__notify(notifications.CollectedFiles(folder_to_files))
        return folder_to_files
