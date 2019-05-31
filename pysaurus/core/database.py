import concurrent.futures
import os
from typing import Dict, List, Union, Optional, Set

import ujson as json

from pysaurus.core import notifications, notifier, thumbnail_utils
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.constants import VIDEO_BATCH_SIZE, PYTHON_ERROR_NOTHING, THUMBNAIL_EXTENSION
from pysaurus.core.duration import Duration
from pysaurus.core.file_size import FileSize
from pysaurus.core.profiler import Profiler
from pysaurus.core.utils import functions as utils
from pysaurus.core.video import Video
from pysaurus.core.video_raptor import api as video_raptor
from pysaurus.core.video_raptor.result import VideoRaptorResult


class Id:
    __slots__ = ('database', 'id')

    def __init__(self, database, video_id):
        # type: (Database, int) -> None
        self.database = database
        self.id = video_id

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    def __str__(self):
        return str(self.id).rjust(len(str(self.database.nb_entries - 1)))

    @staticmethod
    def ensure(database, number):
        if not isinstance(number, Id):
            number = Id(database, number)
        return number


class Database(object):
    __slots__ = ['__list_path', '__json_path', '__database_path', '__folders', '__videos', '__unreadable',
                 '__id_to_file_name', '__file_name_to_id', '__system_is_case_insensitive']

    def __init__(self, list_file_path):
        self.__list_path = AbsolutePath.ensure(list_file_path)
        self.__database_path = self.__list_path.get_directory()
        self.__json_path = AbsolutePath.new_file_path(self.__database_path, self.__list_path.title, 'json')
        self.__folders = utils.load_path_list_file(self.__list_path)
        self.__videos = {}  # type: Dict[AbsolutePath: Video]
        self.__id_to_file_name = {}  # type: Dict[Id, AbsolutePath]
        self.__file_name_to_id = {}  # type: Dict[AbsolutePath, Id]
        self.__unreadable = {}  # type: Dict[AbsolutePath, List[str]]
        self.__system_is_case_insensitive = utils.file_system_is_case_insensitive(self.__database_path.path)
        self.load()

    @property
    def nb_unreadable(self):
        return len(self.__unreadable)

    @property
    def nb_not_found(self):
        return sum(not video.exists() for video in self.__videos.values())

    @property
    def nb_valid(self):
        return sum(video.exists() for video in self.__videos.values())

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

    def get_video_from_id(self, video_id):
        # type: (Union[Id, int]) -> Optional[Video]
        video_id = Id.ensure(self, video_id)
        if video_id in self.__id_to_file_name:
            return self.__videos[self.__id_to_file_name[video_id]]
        return None

    def get_video_id(self, video):
        if video.filename in self.__file_name_to_id:
            return self.__file_name_to_id[video.filename]
        return None

    def update(self):
        folder_to_files = Database.get_videos_paths_from_disk(self.__folders)
        cpu_count = os.cpu_count()
        video_errors = {}
        videos = {}
        all_file_names = [file_name.path
                          for file_names in folder_to_files.values()
                          for file_name in file_names
                          if file_name not in self.__videos and file_name not in self.__unreadable]
        notifier.notify(notifications.VideosToLoad(len(all_file_names)))
        if not all_file_names:
            return

        jobs = utils.dispatch_tasks(all_file_names, cpu_count)
        with Profiler(title='Get videos info (%d threads)' % len(jobs)):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                results = list(executor.map(Database.job_videos_info, jobs))

        for (local_file_names, local_results) in results:  # type: dict
            for file_name, result in zip(local_file_names, local_results):  # type: (str, VideoRaptorResult)
                file_name = AbsolutePath.ensure(file_name)
                if result.done:  # type: Video
                    if result.errors:
                        result.done.errors.update(result.errors)
                    videos[file_name] = result.done
                elif result.errors:
                    video_errors[file_name] = result.errors
                else:
                    video_errors[file_name] = [PYTHON_ERROR_NOTHING]

        assert len(all_file_names) == len(videos) + len(video_errors)
        notifier.notify(notifications.VideosLoaded(len(videos)))

        # Parsing messages.
        if videos:
            self.__videos.update(videos)
        if video_errors:
            self.__unreadable.update(video_errors)
            notifier.notify(notifications.VideoInfoErrors(video_errors))
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

        notifier.notify(notifications.ThumbnailsToLoad(len(videos_without_thumbs)))
        if not videos_without_thumbs:
            self.notify_missing_thumbnails()
            return

        for video in videos_without_thumbs:
            base_thumb_name = thumbnail_utils.ThumbnailStrings.generate_name(video.filename)
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
            thumb_jobs.append((job_file_names, job_thumb_names, self.__database_path.path, job_id))
        with Profiler(title='Get thumbnails through %d thread(s)' % len(thumb_jobs)):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                thumb_results = list(executor.map(Database.job_videos_thumbnails, thumb_jobs))

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

        self.notify_missing_thumbnails()
        if thumb_video_errors:
            notifier.notify(notifications.VideoThumbnailErrors(thumb_video_errors))
        self.save(update_identifiers=False)

    def notify_missing_thumbnails(self):
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
        notifier.notify(notifications.MissingThumbnails(remaining_thumb_videos))

    def __get_thumbnails_names_on_disk(self):
        all_images_paths = []
        for path_string in self.__database_path.listdir():
            if path_string.lower().endswith('.%s' % THUMBNAIL_EXTENSION):
                if self.__system_is_case_insensitive:
                    path_string = path_string.lower()
                all_images_paths.append(path_string[:-(len(THUMBNAIL_EXTENSION) + 1)])
        return set(all_images_paths)

    def clean_unused_thumbnails(self):
        existing_thumb_names = self.__get_thumbnails_names_on_disk()
        for video in self.__videos.values():
            if video.exists() and not video.error_thumbnail:
                thumb_name = video.ensure_thumbnail_name()
                if self.__system_is_case_insensitive:
                    thumb_name = thumb_name.lower()
                if thumb_name in existing_thumb_names:
                    existing_thumb_names.remove(thumb_name)
        notifier.notify(notifications.UnusedThumbnails(len(existing_thumb_names)))
        for unused_thumb_name in existing_thumb_names:
            os.unlink(os.path.join(self.__database_path.path, '%s.%s' % (unused_thumb_name, THUMBNAIL_EXTENSION)))

    def remove_videos_not_found(self, save=False):
        videos_not_found = [video for video in self.__videos.values() if not video.exists()]
        if videos_not_found:
            for video in videos_not_found:
                self.delete_video(video)
            notifier.notify(notifications.VideosNotFoundRemoved(len(videos_not_found)))
            if save:
                self.save()

    def delete_video(self, video):
        # type: (Video) -> None
        if video.filename in self.__videos:
            del self.__videos[video.filename]
            del self.__id_to_file_name[self.__file_name_to_id.pop(video.filename)]
        if video.filename.isfile():
            video.filename.delete()
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
        notifier.notify(notifications.DatabaseLoaded(
            total=self.nb_entries, not_found=self.nb_not_found, unreadable=self.nb_unreadable))

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
            notifier.notify(notifications.DatabaseSaved(self.nb_entries))

    def __generate_identifiers(self):
        self.__id_to_file_name = {Id(self, index): filename for index, filename in enumerate(sorted(self.__videos))}
        self.__file_name_to_id = {filename: index for index, filename in self.__id_to_file_name.items()}

    @staticmethod
    def get_videos_paths_from_disk(paths):
        # type: (Set[AbsolutePath]) -> Dict[AbsolutePath: List[AbsolutePath]]
        folder_to_files = {}
        cpu_count = os.cpu_count()
        jobs = utils.dispatch_tasks(sorted(paths), cpu_count)
        with Profiler(title='Collect videos (%d threads)' % len(jobs)):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                results = list(executor.map(Database.job_collect_videos, jobs))
        for local_result in results:  # type: dict
            for folder, files in local_result.items():
                folder_to_files.setdefault(folder, set()).update(files)
        notifier.notify(notifications.CollectedFiles(folder_to_files))
        return folder_to_files

    @staticmethod
    def job_collect_videos(job):
        folder_to_files = {}
        paths, _ = job
        folders = set()
        for path in paths:  # type: AbsolutePath
            if not path.exists():
                notifier.notify(notifications.FolderNotFound(path))
            elif path.isdir():
                folders.add(path)
            elif utils.is_valid_video_filename(path.path):
                folder_to_files.setdefault(path.get_directory(), set()).add(path)
                notifier.notify(notifications.CollectingFiles(path))
            else:
                notifier.notify(notifications.PathIgnored(path))
        for folder in folders:
            Database.collect_files(folder, folder_to_files)
        return folder_to_files

    @staticmethod
    def job_videos_info(job):
        results = []
        file_names, job_id = job
        count_tasks = len(file_names)
        cursor = 0
        while cursor < count_tasks:
            notifier.notify(notifications.VideoJob(job_id, cursor, count_tasks))
            results.extend(video_raptor.collect_video_info(file_names[cursor:(cursor + VIDEO_BATCH_SIZE)]))
            cursor += VIDEO_BATCH_SIZE
        notifier.notify(notifications.VideoJob(job_id, count_tasks, count_tasks))
        return file_names, results

    @staticmethod
    def job_videos_thumbnails(job):
        results = []
        file_names, thumb_names, thumb_folder, job_id = job
        cursor = 0
        count_tasks = len(file_names)
        while cursor < count_tasks:
            notifier.notify(notifications.ThumbnailJob(job_id, cursor, count_tasks))
            results.extend(
                video_raptor.generate_video_thumbnails(
                    file_names[cursor:(cursor + VIDEO_BATCH_SIZE)],
                    thumb_names[cursor:(cursor + VIDEO_BATCH_SIZE)],
                    thumb_folder))
            cursor += VIDEO_BATCH_SIZE
        notifier.notify(notifications.ThumbnailJob(job_id, count_tasks, count_tasks))
        return file_names, results

    @staticmethod
    def collect_files(folder_path: AbsolutePath, folder_to_files: dict):
        nb_collected = 0
        for file_name in folder_path.listdir():
            path = AbsolutePath.join(folder_path, file_name)
            if path.isdir():
                Database.collect_files(path, folder_to_files)
            elif utils.is_valid_video_filename(path.path):
                folder_to_files.setdefault(folder_path, set()).add(path)
                nb_collected += 1
        if nb_collected:
            notifier.notify(notifications.CollectingFiles(folder_path))
        return nb_collected

    @staticmethod
    def load_from_list_file(list_file_path):
        # type: (AbsolutePath) -> Database
        database = Database(list_file_path)
        database.update()
        database.clean_unused_thumbnails()
        database.ensure_thumbnails()
        return database
