import os
from typing import Dict, Iterable, List, Optional, Set, Union

import ujson as json

from pysaurus.core import exceptions, functions as utils
from pysaurus.core.components import AbsolutePath, DateModified, FilePath, PathType, PathInfo
from pysaurus.core.constants import THUMBNAIL_EXTENSION
from pysaurus.core.database import notifications
from pysaurus.core.database.video import Video
from pysaurus.core.database.video_state import VideoState
from pysaurus.core.modules import ImageUtils, System
from pysaurus.core.native.video_raptor.miniature import Miniature
from pysaurus.core.notification import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.profiling import Profiler
from pysaurus.core.database.jobs import jobs_python
from pysaurus.core.path_tree import PathTree


class VideoPropertyBound:

    def __init__(self, fields):
        self.fields = tuple(fields)
        self.min = {}
        self.max = {}

    def update(self, videos):
        self.min.clear()
        self.max.clear()
        if not isinstance(videos, list):
            videos = list(videos)
        if not videos:
            return
        for field in self.fields:
            min_value = getattr(videos[0], field)
            max_value = min_value
            for i in range(1, len(videos)):
                value = getattr(videos[i], field)
                if value < min_value:
                    min_value = value
                if value > max_value:
                    max_value = value
            self.min[field] = min_value
            self.max[field] = max_value
            # print('BOUNDS', field, min_value, max_value)


class Database:
    __slots__ = ('__db_path', '__thumb_folder', '__json_path', '__miniatures_path', '__log_path',
                 '__date', '__folders', '__videos', '__unreadable', '__discarded',
                 '__notifier', '__id_to_video', 'system_is_case_insensitive', 'video_property_bound')

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
        self.__log_path = FilePath(self.__db_path, self.__db_path.title, 'log')
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
        self.__notifier.set_log_path(self.__log_path.path)
        with Profiler('Load database'):
            self.__load(folders, clear_old_folders)
        self.video_property_bound = VideoPropertyBound(t[0] for t in Video.QUALITY_FIELDS)
        self.video_property_bound.update(self.videos())

    # Properties.

    folder = property(lambda self: self.__db_path)
    nb_entries = property(lambda self: len(self.__videos) + len(self.__unreadable) + len(self.__discarded))
    nb_discarded = property(lambda self: len(self.__discarded))
    nb_unreadable = property(lambda self: len(self.__unreadable))
    nb_not_found = property(lambda self: sum(1 for _ in self.videos(unreadable=True, found=False, not_found=True)))
    nb_found = property(lambda self: sum(1 for _ in self.videos(unreadable=True)))
    nb_valid = property(lambda self: sum(1 for _ in self.videos()))
    nb_thumbnails = property(lambda self: sum(1 for _ in self.videos(no_thumbs=False)))

    @property
    def thumbnail_folder(self):
        if not self.__thumb_folder.isdir():
            self.__thumb_folder.mkdir()
        return self.__thumb_folder

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

        folders_tree = PathTree()
        for f in self.__folders:
            folders_tree.add(f)

        # Parsing videos.
        for video_dict in json_dict.get('videos', ()):
            if video_dict['U']:
                video_state = VideoState.from_dict(video_dict, self)
                destination = self.__unreadable
            else:
                video_state = Video.from_dict(video_dict, self)
                destination = self.__videos
            if folders_tree.in_folders(video_state.filename):
                destination[video_state.filename] = video_state
            else:
                self.__discarded[video_state.filename] = video_state

        self.__set_videos_flags()
        self.__ensure_identifiers()
        self.__notifier.notify(notifications.DatabaseLoaded(self))

    def __set_videos_flags(self):
        self.__set_videos_states_flags()
        self.__set_videos_thumbs_flags()

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

    def __set_videos_states_flags(self):
        file_paths = self.__check_videos_on_disk()
        for dictionaries in (self.__videos, self.__unreadable):
            for video_state in dictionaries.values():
                info = file_paths.get(video_state.filename, None)
                video_state.rt_is_file = info is not None
                if info:
                    video_state.rt_mtime = info.mtime
                    video_state.rt_size = info.size
                    video_state.driver_id = info.driver_id
        return file_paths

    def __set_videos_thumbs_flags(self):
        thumb_names = self.__check_thumbnails_on_disk()
        for video in self.__videos.values():
            video.runtime_has_thumbnail = video.ensure_thumbnail_name() in thumb_names
        return thumb_names

    def __check_videos_on_disk(self):
        # type: () -> Dict[AbsolutePath, PathInfo]
        paths = {}
        cpu_count = os.cpu_count()
        jobs = utils.dispatch_tasks(sorted(self.__folders), cpu_count)
        with Profiler(title='Collect videos (%d threads)' % cpu_count, notifier=self.__notifier):
            results = utils.parallelize(jobs_python.job_collect_videos_info, jobs, cpu_count)
        for local_result in results:  # type: List[PathInfo]
            for info in local_result:
                paths[info.path] = info
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

    def __filter_not_found(self, video):
        return not video.exists()

    def __filter_found(self, video):
        return video.exists()

    def __filter_no_thumbs(self, video):
        return not video.thumbnail_is_valid()

    def __filter_with_thumbs(self, video):
        return video.thumbnail_is_valid()

    def __notify_missing_thumbnails(self):
        remaining_thumb_videos = []
        for video in self.__videos.values():
            if video.exists() and not video.thumbnail_is_valid():
                remaining_thumb_videos.append(video.filename.path)
        self.__notifier.notify(notifications.MissingThumbnails(remaining_thumb_videos))

    # Public methods.

    def update(self):
        cpu_count = os.cpu_count()
        current_date = DateModified.now()
        all_file_names = self.get_new_video_paths()

        self.__notifier.notify(notifications.VideosToLoad(len(all_file_names)))
        if not all_file_names:
            return

        pre_jobs = utils.dispatch_tasks(all_file_names, cpu_count)
        jobs = []
        for index, (file_names, job_id) in enumerate(pre_jobs):
            input_file_path = FilePath(self.__db_path, str(index), 'list')
            output_file_path = FilePath(self.__db_path, str(index), 'json')

            with open(input_file_path.path, 'wb') as file:
                for file_name in file_names:
                    file.write(('%s\n' % file_name).encode())

            jobs.append((input_file_path.path, output_file_path.path, len(file_names), job_id, self.__notifier))

        with Profiler(title='Get videos info from JSON (%d threads)' % len(jobs), notifier=self.__notifier):
            counts_loaded = utils.parallelize(jobs_python.job_video_to_json, jobs, cpu_count=cpu_count)

        videos = {}
        unreadable = {}
        for job in jobs:
            list_file_path = AbsolutePath.ensure(job[0])
            json_file_path = AbsolutePath.ensure(job[1])
            assert json_file_path.isfile()
            with open(json_file_path.path, encoding='utf-8') as file:
                arr = json.load(file)
            for d in arr:
                file_path = AbsolutePath.ensure(d['f'])
                stat = os.stat(file_path.path)
                if len(d) == 2:
                    video_state = VideoState(
                        filename=file_path, size=file_path.get_size(), errors=d['e'], database=self)
                    unreadable[file_path] = video_state
                    self.__videos.pop(file_path, None)
                else:
                    video_state = Video.from_dict(d, self)
                    videos[file_path] = video_state
                    self.__unreadable.pop(file_path, None)
                video_state.rt_is_file = True
                video_state.rt_size = stat.st_size
                video_state.rt_mtime = stat.st_mtime
                video_state.driver_id = stat.st_dev

            list_file_path.delete()
            json_file_path.delete()
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
            if video.exists() and not video.error_thumbnail:
                thumb_name = video.ensure_thumbnail_name()
                if thumb_name in existing_thumb_names and video.thumbnail_path.get_date_modified() > video.filename.get_date_modified():
                    thumb_to_videos.setdefault(thumb_name, []).append(video)
                else:
                    videos_without_thumbs.append(video)

        # If a thumbnail name is associated to many videos,
        # consider these videos don't have thumbnails.
        for valid_thumb_name, vds in thumb_to_videos.items():
            if len(vds) == 1:
                valid_thumb_names.add(valid_thumb_name)
                vds[0].runtime_has_thumbnail = True
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
            video.runtime_has_thumbnail = True
            valid_thumb_names.add(thumb_name)
        del valid_thumb_names
        self.save()

        dispatched_thumb_jobs = utils.dispatch_tasks(videos_without_thumbs, cpu_count)
        del videos_without_thumbs
        for index, (job_videos, job_id) in enumerate(dispatched_thumb_jobs):
            input_file_path = FilePath(self.__db_path, str(index), 'thumbnails.list')
            output_file_path = FilePath(self.__db_path, str(index), 'thumbnails.json')

            with open(input_file_path.path, 'wb') as file:
                for video in job_videos:
                    file.write(('%s\t%s\t%s\t\n' % (video.filename, self.__thumb_folder, video.thumb_name)).encode())

            thumb_jobs.append((input_file_path.path, output_file_path.path, len(job_videos), job_id, self.__notifier))

        with Profiler(title='Get thumbnails from JSON through %d thread(s)' % len(thumb_jobs), notifier=self.__notifier):
            counts_loaded = utils.parallelize(jobs_python.job_video_thumbnails_to_json, thumb_jobs, cpu_count=cpu_count)

        for job in thumb_jobs:
            list_file_path = AbsolutePath.ensure(job[0])
            json_file_path = AbsolutePath.ensure(job[1])
            assert json_file_path.isfile()

            with open(json_file_path.path, encoding='utf-8') as file:
                arr = json.load(file)
            for d in arr:
                if d is not None:
                    assert len(d) == 2 and 'f' in d and 'e' in d
                    file_name = d['f']
                    file_path = AbsolutePath.ensure(file_name)
                    thumb_errors[file_name] = d['e']
                    video = self.__videos[file_path]
                    video.error_thumbnail = True
                    video.runtime_has_thumbnail = False

            list_file_path.delete()
            json_file_path.delete()

        assert sum(counts_loaded) + len(thumb_errors) == nb_videos_no_thumbs

        if thumb_errors:
            self.__notifier.notify(notifications.VideoThumbnailErrors(thumb_errors))

        self.__notify_missing_thumbnails()
        self.save()

    def ensure_miniatures(self, return_miniatures=False):
        # type: (bool) -> Optional[List[Miniature]]

        identifiers = set()
        valid_dictionaries = []
        added_miniatures = []
        have_removed = False
        have_added = False

        if self.__miniatures_path.exists():
            if not self.__miniatures_path.isfile():
                raise exceptions.NotFileError(self.__miniatures_path)
            with open(self.__miniatures_path.path, 'r') as miniatures_file:
                json_array = json.load(miniatures_file)
            if not isinstance(json_array, list):
                raise exceptions.PysaurusError('Miniatures file does not contain a list.')
            for dct in json_array:
                video = self.get_video_from_filename(dct['i'], required=False)
                if (video
                        and video.exists()
                        and ImageUtils.DEFAULT_THUMBNAIL_SIZE == (dct['w'], dct['h'])):
                    identifiers.add(video.filename.path)
                    valid_dictionaries.append(dct)
            have_removed = len(valid_dictionaries) != len(json_array)
            del json_array

        tasks = [(video.filename, video.thumbnail_path)
                 for video in self.videos(no_thumbs=False)
                 if video.filename.path not in identifiers]
        self.__notifier.notify(notifications.MiniaturesToLoad(len(tasks)))

        if tasks:
            have_added = True
            cpu_count = os.cpu_count()
            jobs = utils.dispatch_tasks(tasks, cpu_count, extra_args=[self.__notifier])
            del tasks
            with Profiler('Generating miniatures.'):
                results = utils.parallelize(jobs_python.job_generate_miniatures, jobs, cpu_count)
            del jobs
            for local_array in results:
                added_miniatures.extend(local_array)
            del results

        if have_removed or have_added:
            with open(self.__miniatures_path.path, 'w') as output_file:
                json.dump(valid_dictionaries + [m.to_dict() for m in added_miniatures], output_file)

        self.__notifier.notify(notifications.NbMiniatures(len(valid_dictionaries) + len(added_miniatures)))

        if return_miniatures:
            return [Miniature.from_dict(d) for d in valid_dictionaries] + added_miniatures

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

    def change_video_file_title(self, video, new_title):
        # type: (Video, str) -> None
        discarded_characters = r'@#\\/?$'
        if video.filename.title != new_title:
            if any(c in new_title for c in discarded_characters):
                raise OSError('Characters not allowed: %s' % discarded_characters)
            new_filename = video.filename.new_title(new_title)
            if video.filename in self.__videos:
                del self.__videos[video.filename]
                self.__videos[new_filename] = video
                video.filename = new_filename
                self.save()

    def remove_videos_not_found(self):
        nb_removed = 0
        for video in list(self.__videos.values()):
            if not video.filename.isfile():
                self.delete_video(video, save=False)
                nb_removed += 1
        if nb_removed:
            self.__notifier.notify(notifications.VideosNotFoundRemoved(nb_removed))
            self.save()

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

    def get_unreadable_from_filename(self, filename, required=True):
        # type: (PathType, bool) -> Optional[VideoState]
        filename = AbsolutePath.ensure(filename)
        if filename in self.__unreadable:
            return self.__unreadable[filename]
        if required:
            raise exceptions.UnknownVideoFilename(filename)
        return None


    def delete_video(self, video, save=True):
        # type: (VideoState, bool) -> AbsolutePath
        video.filename.delete()
        self.__videos.pop(video.filename, None)
        self.__unreadable.pop(video.filename, None)
        self.__discarded.pop(video.filename, None)
        self.__id_to_video.pop(video.video_id, None)
        if isinstance(video, Video):
            video.thumbnail_path.delete()
        if save:
            self.save()
        return video.filename

    def save(self):
        self.__ensure_identifiers()
        self.video_property_bound.update(self.videos())
        # Save database.
        json_output = {'date': self.__date.time,
                       'folders': sorted(folder.path for folder in self.__folders),
                       'videos': sorted(
                           (video.to_dict()
                            for dct in (self.__videos, self.__unreadable, self.__discarded)
                            for video in dct.values()),
                           key=lambda dct: dct['f'])}
        with open(self.__json_path.path, 'w') as output_file:
            json.dump(json_output, output_file)
        self.__notifier.notify(notifications.DatabaseSaved(self))

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

    def get_new_video_paths(self):
        all_file_names = []

        file_names = self.__set_videos_states_flags()

        for file_name in file_names:  # type: AbsolutePath
            video_state = None
            if file_name in self.__videos:
                video_state = self.__videos[file_name]
            elif file_name in self.__unreadable:
                video_state = self.__unreadable[file_name]

            if (not video_state
                    or video_state.date >= self.__date
                    or video_state.rt_size != video_state.file_size):
                all_file_names.append(file_name.path)

        all_file_names.sort()
        return all_file_names

    def get_video_from_filename(self, filename, required=True):
        # type: (PathType, bool) -> Optional[Video]
        filename = AbsolutePath.ensure(filename)
        if filename in self.__videos:
            return self.__videos[filename]
        if required:
            raise exceptions.UnknownVideoFilename(filename)
        return None

    # Unused.

    def clean_unused_thumbnails(self):
        used_thumbnails = set()
        for video in self.__videos.values():
            if video.exists() and video.thumbnail_is_valid():
                used_thumbnails.add(video.ensure_thumbnail_name())
        unused_thumbnails = self.__check_thumbnails_on_disk() - used_thumbnails
        self.__notifier.notify(notifications.UnusedThumbnails(len(unused_thumbnails)))
        for unused_thumb_name in unused_thumbnails:
            try:
                FilePath(self.__thumb_folder, unused_thumb_name, THUMBNAIL_EXTENSION).delete()
            except OSError:
                pass
