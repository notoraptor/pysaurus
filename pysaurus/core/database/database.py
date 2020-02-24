import os
from typing import Dict, Iterable, List, Optional, Set, Union

import ujson as json

from pysaurus.core.database.jobs import jobs_python, jobs_video_raptor
from pysaurus.core import exceptions, functions as utils
from pysaurus.core.components import AbsolutePath, DateModified, FilePath, PathType
from pysaurus.core.constants import PYTHON_ERROR_NOTHING, THUMBNAIL_EXTENSION
from pysaurus.core.database import notifications
from pysaurus.core.database.video import Video
from pysaurus.core.database.video_state import VideoState
from pysaurus.core.modules import ImageUtils, System
from pysaurus.core.native.video_raptor.api import VideoRaptorResult
from pysaurus.core.native.video_raptor.miniature import Miniature
from pysaurus.core.notification import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.profiling import Profiler
from pysaurus.core.database.jobs import async_jobs as job_module, jobs_python


class Database:
    __slots__ = ['__db_path', '__thumb_folder', '__json_path', '__miniatures_path',
                 '__date', '__folders', '__videos', '__unreadable', '__discarded',
                 '__notifier', '__id_to_video', 'system_is_case_insensitive']

    def __init__(self, path, folders=None, clear_old_folders=False, notifier=None):
        # type: (PathType, Optional[Iterable[PathType]], Optional[bool], Optional[Notifier]) -> None
        path = AbsolutePath.ensure(path)
        if not path.isdir():
            raise exceptions.NotDirectoryError(path)
        # Paths
        self.__db_path = path
        self.__thumb_folder = AbsolutePath.join(self.__db_path, '%s.thumbnails' % self.__db_path.title)
        self.__json_path = FilePath(self.__db_path, self.__db_path.title, 'json')
        self.__miniatures_path = FilePath(self.__db_path, '%s.miniatures' % self.__db_path.title, 'json')
        # Database data
        self.__date = DateModified.now()
        self.__folders = set()  # type: Set[AbsolutePath]
        self.__videos = {}  # type: Dict[AbsolutePath, Video]
        self.__unreadable = {}  # type: Dict[AbsolutePath, VideoState]
        self.__discarded = {}  # type: Dict[AbsolutePath, VideoState]
        # RAM data
        self.__notifier = notifier or DEFAULT_NOTIFIER
        self.__id_to_video = {}  # type: Dict[int, Union[VideoState, Video]]
        self.system_is_case_insensitive = System.is_case_insensitive(self.__db_path.path)
        # Load database
        self.__load(folders, clear_old_folders)

    # Properties.

    folder = property(lambda self: self.__db_path)
    nb_entries = property(lambda self: len(self.__videos) + len(self.__unreadable) + len(self.__discarded))
    nb_discarded = property(lambda self: len(self.__discarded))
    nb_unreadable = property(lambda self: len(self.__unreadable))
    nb_not_found = property(lambda self: sum(1 for _ in self.videos(unreadable=True, found=False, not_found=True)))
    nb_found = property(lambda self: sum(1 for _ in self.videos(valid=True, unreadable=True)))
    nb_valid = property(lambda self: sum(1 for _ in self.videos()))
    nb_thumbnails = property(lambda self: sum(1 for _ in self.videos(no_thumbs=False)))

    @property
    def thumbnail_folder(self):
        if not self.__thumb_folder.isdir():
            self.__thumb_folder.mkdir()
        return self.__thumb_folder

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

    def __check_videos_on_disk(self):
        # type: () -> Set[AbsolutePath]
        paths = set()
        cpu_count = os.cpu_count()
        jobs = utils.dispatch_tasks(sorted(self.__folders), cpu_count)
        with Profiler(title='Collect videos (%d threads)' % cpu_count, notifier=self.__notifier):
            results = utils.parallelize(jobs_python.job_collect_videos, jobs, cpu_count)
        for local_result in results:  # type: List[AbsolutePath]
            paths.update(local_result)
        self.__notifier.notify(notifications.FinishedCollectingVideos(paths))
        return paths

    def __check_thumbnails_on_disk(self):
        # type: () -> Set[str]
        thumbs = set()
        with Profiler('Collect thumbnails', self.__notifier):
            for path_string in self.thumbnail_folder.listdir():
                if path_string.lower().endswith('.%s' % THUMBNAIL_EXTENSION):
                    if self.system_is_case_insensitive:
                        path_string = path_string.lower()
                    thumbs.add(path_string[:-(len(THUMBNAIL_EXTENSION) + 1)])
        return thumbs

    def __notify_missing_thumbnails(self):
        remaining_thumb_videos = []
        for video in self.__videos.values():
            if (self.video_exists(video.filename)
                    and (video.error_thumbnail
                         or not video.thumbnail_path.isfile())):
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

        self.__notifier.notify(notifications.DatabaseLoaded(self))
        self.__ensure_identifiers()

    def __ensure_identifiers(self):
        without_identifiers = []
        for source in (self.__videos, self.__unreadable):
            for video_state in source.values():
                if (not isinstance(video_state.video_id, int)
                        or video_state.video_id in self.__id_to_video):
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

    def get_new_video_paths(self):
        all_file_names = []

        file_names = self.__check_videos_on_disk()

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

        all_file_names.sort()
        return all_file_names

    def update(self):
        cpu_count = os.cpu_count()
        all_file_names = self.get_new_video_paths()
        current_date = DateModified.now()

        self.__notifier.notify(notifications.VideosToLoad(len(all_file_names)))
        if not all_file_names:
            return

        pre_jobs = utils.dispatch_tasks(all_file_names, cpu_count)
        jobs = []
        for index, (file_names, job_id) in enumerate(pre_jobs):
            input_file_path = FilePath(self.__db_path, str(index), 'list')
            output_file_path = FilePath(self.__db_path, str(index), 'jsonl')

            with open(input_file_path.path, 'wb') as file:
                for file_name in file_names:
                    file.write(('%s\n' % file_name).encode())

            jobs.append((
                input_file_path.path,
                output_file_path.path,
                len(file_names),
                job_id,
                self.__notifier
            ))

        with Profiler(title='Get videos info from JSON (%d threads)' % len(jobs), notifier=self.__notifier):
            counts_loaded = job_module.batch(job_module.job_video_to_json, jobs, cpu_count=cpu_count)

        videos = {}
        unreadable = {}
        for job in jobs:
            list_file_path = AbsolutePath.ensure(job[0])
            jsonl_file_path = AbsolutePath.ensure(job[1])
            assert jsonl_file_path.isfile()
            with open(jsonl_file_path.path, encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        d = json.loads(line)
                        file_path = AbsolutePath.ensure(d['f'])
                        if len(d) == 2:
                            unreadable[file_path] = VideoState(
                                filename=file_path,
                                size=file_path.get_size(),
                                errors=d['e'],
                                database=self)
                        else:
                            videos[file_path] = Video.from_dict(d, self)
            list_file_path.delete()
            jsonl_file_path.delete()
        assert sum(counts_loaded) == len(videos)
        assert len(videos) + len(unreadable) == len(all_file_names)

        if videos:
            self.__videos.update(videos)
        if unreadable:
            self.__unreadable.update(unreadable)
        if videos or unreadable:
            self.__date = current_date
            self.save()
        if unreadable:
            self.__notifier.notify(notifications.VideoInfoErrors(
                {file_name: video_state.errors for file_name, video_state in unreadable.items()}))

    def ensure_thumbnails(self):
        cpu_count = os.cpu_count()
        valid_thumb_names = set()
        videos_without_thumbs = []
        thumb_to_videos = {}
        thumb_errors = {}
        thumb_jobs = []

        # Collect videos with and without thumbnails.
        existing_thumb_names = self.__check_thumbnails_on_disk()

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
        for index, (job_videos, job_id) in enumerate(dispatched_thumb_jobs):
            input_file_path = FilePath(self.__db_path, str(index), 'thumbnails.list')
            output_file_path = FilePath(self.__db_path, str(index), 'thumbnails.jsonl')

            with open(input_file_path.path, 'wb') as file:
                for video in job_videos:
                    file.write(('%s\t%s\t%s\t\n' % (video.filename, self.__thumb_folder, video.thumb_name)).encode())

            thumb_jobs.append((
                input_file_path.path,
                output_file_path.path,
                len(job_videos),
                job_id,
                self.__notifier
            ))

        with Profiler(title='Get thumbnails from JSON through %d thread(s)' % len(thumb_jobs), notifier=self.__notifier):
            counts_loaded = job_module.batch(job_module.job_video_thumbnails_to_json, thumb_jobs, cpu_count=cpu_count)

        for job in thumb_jobs:
            list_file_path = AbsolutePath.ensure(job[0])
            jsonl_file_path = AbsolutePath.ensure(job[1])
            assert jsonl_file_path.isfile()

            with open(jsonl_file_path.path, encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        d = json.loads(line)
                        assert len(d) == 2 and 'f' in d and 'e' in d
                        file_name = d['f']
                        file_path = AbsolutePath.ensure(file_name)
                        thumb_errors[file_name] = d['e']
                        self.__videos[file_path].error_thumbnail = True

            list_file_path.delete()
            jsonl_file_path.delete()

        assert sum(counts_loaded) + len(thumb_errors) == nb_videos_no_thumbs

        if thumb_errors:
            self.__notifier.notify(notifications.VideoThumbnailErrors(thumb_errors))

        self.__notify_missing_thumbnails()
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
                video = self.get_video_from_filename(dct['i'], required=False)
                if (video
                        and self.video_exists(video.filename)
                        and ImageUtils.DEFAULT_THUMBNAIL_SIZE == (dct['w'], dct['h'])):
                    miniature = Miniature.from_dict(dct)
                    miniatures[miniature.identifier] = miniature
            del json_dict
        tasks = [(video.filename, video.thumbnail_path)
                 for video in self.videos(no_thumbs=False)
                 if video.filename.path not in miniatures]
        print('Missing', len(tasks), '/', len(tasks) + len(miniatures), 'miniature(s).')
        if not tasks:
            return miniatures
        cpu_count = os.cpu_count()
        jobs = utils.dispatch_tasks(tasks, cpu_count)
        del tasks
        with Profiler('Generating miniatures.'):
            results = utils.parallelize(jobs_python.job_generate_miniatures, jobs, cpu_count)
        del jobs
        for local_array in results:
            for miniature in local_array:  # type: Miniature
                miniature.identifier = miniature.identifier.path
                miniatures[miniature.identifier] = miniature
        del results
        with open(self.__miniatures_path.path, 'w') as output_file:
            json.dump([miniatures[identifier].to_dict() for identifier in sorted(miniatures)], output_file)
        return miniatures

    def list_files(self, output_name):
        with open(output_name, 'wb') as file:
            file.write('# Videos\n'.encode())
            for file_name in sorted(self.__videos):
                file.write(('%s\n' % str(file_name)).encode())
            file.write('# Unreadable\n'.encode())
            for file_name in sorted(self.__unreadable):
                file.write(('%s\n' % str(file_name)).encode())
            file.write('# Discarded\n'.encode())
            for file_name in sorted(self.__discarded):
                file.write(('%s\n' % str(file_name)).encode())

    def reset(self, reset_thumbnails=False, reset_miniatures=False):
        self.__videos.clear()
        self.__unreadable.clear()
        self.__discarded.clear()
        self.__json_path.delete()
        if reset_miniatures:
            self.__miniatures_path.delete()
        if reset_thumbnails:
            self.__thumb_folder.delete()

    # Public features.

    def video_exists(self, path: AbsolutePath):
        return path.isfile()

    def get_video_from_id(self, video_id, required=True):
        # type: (int, bool) -> Optional[Video]
        if (video_id in self.__id_to_video
                and self.__id_to_video[video_id].filename in self.__videos):
            return self.__id_to_video[video_id]
        if required:
            raise exceptions.UnknownVideoID(video_id)
        return None

    def get_unreadable_from_id(self, video_id, required=True):
        # type: (int, bool) -> Optional[VideoState]
        if (video_id in self.__id_to_video
                and self.__id_to_video[video_id].filename in self.__unreadable):
            return self.__id_to_video[video_id]
        if required:
            raise exceptions.UnknownVideoID(video_id)
        return None

    def get_video_from_filename(self, filename, required=True):
        # type: (PathType, bool) -> Optional[Video]
        filename = AbsolutePath.ensure(filename)
        if filename in self.__videos:
            return self.__videos[filename]
        if required:
            raise exceptions.UnknownVideoFilename(filename)
        return None

    def get_unreadable_from_filename(self, filename, required=True):
        # type: (PathType, bool) -> Optional[VideoState]
        filename = AbsolutePath.ensure(filename)
        if filename in self.__unreadable:
            return self.__unreadable[filename]
        if required:
            raise exceptions.UnknownVideoFilename(filename)
        return None

    def remove_videos_not_found(self):
        nb_removed = 0
        for video in list(self.__videos.values()):
            if not video.filename.isfile():
                self.delete_video(video, save=False)
                nb_removed += 1
        if nb_removed:
            self.__notifier.notify(notifications.VideosNotFoundRemoved(nb_removed))
            self.save()

    def delete_video(self, video, save=True):
        # type: (VideoState, bool) -> AbsolutePath
        if video.filename.isfile():
            video.filename.delete()
        if video.filename in self.__videos:
            del self.__videos[video.filename]
            if isinstance(video, Video):
                del self.__id_to_video[video.video_id]
        if isinstance(video, Video):
            video.thumbnail_path.delete()
        if save:
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
        used_thumbnails = set()
        for video in self.__videos.values():
            if self.video_exists(video.filename) and not video.error_thumbnail:
                thumb_name = video.ensure_thumbnail_name()
                if video.thumbnail_path.isfile():
                    used_thumbnails.add(thumb_name)
        unused_thumbnails = self.__check_thumbnails_on_disk() - used_thumbnails
        self.__notifier.notify(notifications.UnusedThumbnails(len(unused_thumbnails)))
        for unused_thumb_name in unused_thumbnails:
            try:
                FilePath(self.__thumb_folder,
                         unused_thumb_name,
                         THUMBNAIL_EXTENSION).delete()
            except OSError:
                pass
