import sys
import textwrap
import traceback
import ujson as json
from enum import IntEnum, auto
from io import StringIO
from typing import Optional, IO

from pysaurus.new_video import NewVideo
from pysaurus.property import PropertyTypeDict, PropertyDict
from pysaurus.utils import exceptions, ffmpeg_backend
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.profiling import Profiler
from pysaurus.utils.symbols import is_valid_video_filename
from pysaurus.video import Video


class LoadStatus(IntEnum):
    UNLOADED = auto()
    UPDATED = auto()
    LOADED = auto()


class DiskReport(object):
    __slots__ = ('folder_path', 'n_files_checked', 'files_skipped', 'errors', 'updated', 'n_loaded')

    def __init__(self, folder_path):
        self.folder_path = AbsolutePath.ensure(folder_path)
        self.files_skipped = []
        self.errors = []
        self.updated = []
        self.n_files_checked = 0
        self.n_loaded = 0

    def __bool__(self):
        return any(bool(getattr(self, name)) for name in self.__slots__[1:])

    def __str__(self):
        string_pieces = []
        longest_printed_name_length = 0
        string_version = StringIO()  # type: Optional[IO[str]]
        for name in self.__slots__[1:]:
            value = getattr(self, name)
            value_length = value if isinstance(value, int) else len(value)
            if value_length:
                string_pieces.append((name, value_length))
                longest_printed_name_length = max(longest_printed_name_length, len(name))
        print(self.__class__.__name__, file=string_version, end='')
        if longest_printed_name_length:
            string_format = '\t{:<%d}:\t{}' % (longest_printed_name_length + 1)
            print(' (%s) {' % self.folder_path, file=string_version)
            for name, value_length in string_pieces:
                print(string_format.format(name, value_length), file=string_version)
            print('}', file=string_version, end='')
        else:
            print(' (%s) {}' % self.folder_path, file=string_version, end='')
        output_string = string_version.getvalue()
        string_version.close()
        return output_string


class DatabaseReport(object):
    __slots__ = ('disk', 'n_files_checked', 'files_skipped', 'errors', 'removed', 'not_found', 'n_loaded', 'n_saved')

    def __init__(self):
        self.files_skipped = []
        self.errors = []
        self.removed = []
        self.not_found = []
        self.n_files_checked = 0
        self.n_loaded = 0
        self.n_saved = 0
        self.disk = {}  # type: dict{AbsolutePath, DiskReport}

    def __bool__(self):
        return (any(bool(getattr(self, name)) for name in self.__slots__[1:])
                or any(bool(disk_report) for disk_report in self.disk.values()))

    def __str__(self):
        string_pieces = []
        string_version = StringIO()  # type: Optional[IO[str]]
        longest_printed_name_length = 0
        for name in self.__slots__[1:]:
            value = getattr(self, name)
            value_length = value if isinstance(value, int) else len(value)
            if value_length:
                string_pieces.append((name, value_length))
                longest_printed_name_length = max(longest_printed_name_length, len(name))
        print(self.__class__.__name__, file=string_version, end='')
        if longest_printed_name_length or self.disk:
            print(' {', file=string_version)
            if longest_printed_name_length:
                string_format = '\t{:<%d}:\t{}' % (longest_printed_name_length + 1)
                for name, value_length in string_pieces:
                    print(string_format.format(name, value_length), file=string_version)
            if self.disk:
                for key in sorted(self.disk.keys()):
                    print(textwrap.indent(str(self.disk[key]), '\t'), file=string_version)
            print('}', file=string_version, end='')
        else:
            print(' {}', file=string_version)
        output_string = string_version.getvalue()
        string_version.close()
        return output_string


class VideoSet(object):
    __slots__ = '__videos',

    def __init__(self):
        self.__videos = {}  # type: dict{AbsolutePath, Video}

    def add(self, video: Video):
        assert video.absolute_path not in self.__videos
        self.__videos[video.absolute_path] = video

    def remove_from_absolute_path(self, absolute_path: AbsolutePath):
        self.__videos.pop(absolute_path)

    def remove_from_path_string(self, path_string: str):
        self.__videos.pop(AbsolutePath(path_string))

    def contains(self, video: Video):
        return video.absolute_path in self.__videos

    def contains_absolute_path(self, absolute_path: AbsolutePath):
        return absolute_path in self.__videos

    def contains_path_string(self, path_string: str):
        return AbsolutePath(path_string) in self.__videos

    def get_from_absolute_path(self, absolute_path: AbsolutePath):
        """ Return Video associated to given absolute path.
            Raise an error if this path is not associated to any video object in database,
        :param absolute_path: absolute path for video to get Video object.
        :return: a Video object.
        :rtype: Video
        """
        return self.__videos[absolute_path]

    def get_from_path_string(self, path_string: str):
        return self.__videos[AbsolutePath(path_string)]

    def videos(self):
        return self.__videos.values()


class VideoLoader(object):
    __slots__ = '__paths_buffer', '__size'

    def __init__(self, size=25):
        self.__paths_buffer = []
        self.__size = size

    def __flush(self):
        if len(self.__paths_buffer) == self.__size:
            # TODO Load videos.
            self.__paths_buffer.clear()

    def add(self, video_path: AbsolutePath):
        if len(self.__paths_buffer) == self.__size:
            self.__flush()
        self.__paths_buffer.append(video_path)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class Database(VideoSet):
    __slots__ = {'folder_path', 'file_path', 'video_folder_paths', 'property_types', '__max_id'}
    FILE_EXTENSION = 'json'
    FILE_DOT_EXTENSION = '.%s' % FILE_EXTENSION

    def __init__(self, db_folder_path: AbsolutePath, video_folder_names=(), reset_paths=False):
        super(Database, self).__init__()
        db_file_path = AbsolutePath.new_file_path(db_folder_path, db_folder_path.title, self.FILE_EXTENSION)
        if db_file_path.exists():
            with open(db_file_path.path, 'rb') as db_file:
                json_info = json.load(db_file)
            assert json_info['name'] == db_folder_path.title
            video_folder_paths = set()
            if not reset_paths:
                video_folder_paths.update(AbsolutePath(path) for path in json_info['video_folders'])
            property_types = PropertyTypeDict.from_json_data(json_info['property_types'])
            video_folder_paths.update(AbsolutePath.ensure(path) for path in video_folder_names)
        else:
            video_folder_paths = {AbsolutePath.ensure(path) for path in video_folder_names}
            property_types = PropertyTypeDict()
        self.folder_path = db_folder_path
        self.file_path = db_file_path
        self.video_folder_paths = video_folder_paths
        self.property_types = property_types  # type: PropertyTypeDict
        self.__max_id = 0
        self.__load()

    name = property(lambda self: self.folder_path.title)

    def __load(self):
        report = DatabaseReport()
        self.ensure_database_folder()
        try:
            self.__load_videos_from_database(report)
            self.__collect_videos_from_disk()
        finally:
            self.save()
        # self.check_thumbnails()

    def reset_paths(self, video_folder_names=()):
        self.video_folder_paths.clear()
        self.video_folder_paths.update(AbsolutePath.ensure(path) for path in video_folder_names)
        self.__load()

    def __delete_entry(self, video: Video, remove_video_definitively=False):
        entry_path = AbsolutePath.new_file_path(self.folder_path, video.video_id, self.FILE_EXTENSION)
        assert entry_path.exists() and entry_path.isfile()
        entry_path.delete()
        video.delete_thumbnail()
        assert not entry_path.exists()
        if self.contains_absolute_path(video.absolute_path):
            self.remove_from_absolute_path(video.absolute_path)
        if remove_video_definitively:
            video.absolute_path.delete()
            assert not video.absolute_path.exists()

    def __load_videos_from_database(self, report: DatabaseReport = None):
        if report is None:
            report = DatabaseReport()
        for file_name_from_db_folder in self.folder_path.listdir():
            if file_name_from_db_folder != self.file_path.basename:
                report.n_files_checked += 1
                if not file_name_from_db_folder.endswith(self.FILE_DOT_EXTENSION):
                    report.files_skipped.append(file_name_from_db_folder)
                    continue
                db_video_path = AbsolutePath.join(self.folder_path, file_name_from_db_folder)
                try:
                    with open(db_video_path.path, 'rb') as db_video_file:
                        json_info = json.load(db_video_file)
                    video = Video.from_json_data(json_info, self.property_types)
                    if video.video_id is None:
                        raise exceptions.VideoIdException()
                    if video.absolute_path.get_dirname() not in self.video_folder_paths:
                        report.removed.append(video)
                        self.__delete_entry(video)
                        continue
                    if self.contains(video):
                        raise exceptions.DuplicateEntryException()
                    if not video.absolute_path.exists() or not video.absolute_path.isfile():
                        report.not_found.append(video)
                        self.__delete_entry(video)
                        continue
                    self.__max_id = max(self.__max_id, video.video_id)
                    self.add(video)
                    video.updated = False
                    report.n_loaded += 1
                except Exception as e:
                    db_video_path.delete()
                    report.errors.append((db_video_path, e))
        return report

    def __load_video(self, video_path: AbsolutePath):
        """ Load one video from disk to the database.
        :param video_path: path to video to load.
        :return: a LoadStatus value.
        :rtype: LoadStatus
        """
        load_status = LoadStatus.UNLOADED
        if not self.contains_absolute_path(video_path) or (
                video_path.get_date_modified() != self.get_from_absolute_path(video_path).date_modified):
            new_id = self.__max_id + 1
            new_video = NewVideo(video_path.path, video_id=new_id)
            if self.contains_absolute_path(video_path):
                new_video.set_properties(self.get_from_absolute_path(video_path).properties)
                load_status = LoadStatus.UPDATED
            else:
                new_video.set_properties(PropertyDict(self.property_types))
                load_status = LoadStatus.LOADED
            self.add(new_video)
            self.__max_id = new_id
        return load_status

    def __collect_videos_from_folder(self, video_folder_path: AbsolutePath, collection: list, ignored: list = None):
        for file_name in video_folder_path.listdir():
            file_path = AbsolutePath.join(video_folder_path, file_name)
            if file_path.isdir():
                self.__collect_videos_from_folder(file_path, collection)
            elif file_path.isfile() and is_valid_video_filename(file_name):
                collection.append(file_path)
            elif ignored is not None:
                ignored.append(file_path)

    def __collect_videos_from_disk(self):
        collection_list = []
        ignored_list = []
        with Profiler(exit_message='Videos collected from disk:'):
            for video_folder_path in sorted(self.video_folder_paths):
                local_collection = []
                local_ignored = []
                print('Collecting videos in folder', video_folder_path)
                self.__collect_videos_from_folder(video_folder_path, local_collection, local_ignored)
                print('\t', len(local_collection), ' collected, ', len(local_ignored), ' ignored.', sep='')
                collection_list.extend(local_collection)
                ignored_list.extend(local_ignored)
        print('Total:', len(collection_list), 'collected,', len(ignored_list), 'ignored.')
        if ignored_list:
            print('Ignored:')
            for ignored_path in ignored_list:
                print('\t%s' % ignored_path)
        if collection_list:
            print('Loading videos.')
            load_statuses = {status: 0 for status in LoadStatus}
            errors = []
            with Profiler(exit_message='Finished to load %d videos:' % len(collection_list)):
                for index, video_path in enumerate(collection_list):
                    try:
                        load_statuses[self.__load_video(video_path)] += 1
                    except Exception as exception:
                        errors.append((video_path, exception))
                    if (index + 1) % 25 == 0:
                        print(index + 1, 'videos loaded.')
            for status, count in load_statuses.items():
                print(status.name, count)
            if errors:
                print(len(errors), 'error(s) occurred while loading videos.')
                for video_path, exception in errors:
                    print('=' * len(video_path.path))
                    print(video_path)
                    traceback.print_tb(exception.__traceback__, file=sys.stdout)
                    print(exception.__class__.__name__, exception)

    def check_thumbnails(self):
        for index, video in enumerate(self.videos()):  # type: (int, Video)
            if not video.has_valid_thumbnail():
                print('(%d) Creating thumbnail:' % (index + 1), video.absolute_path)
                video.set_thumbnail(ffmpeg_backend.create_thumbnail(video, self.folder_path, video.video_id))

    def ensure_database_folder(self):
        if not self.folder_path.exists():
            self.folder_path.mkdir()
        assert self.folder_path.isdir()

    def save_database_file(self):
        self.ensure_database_folder()
        json_info = {
            'name': self.name,
            'video_folders': [str(path) for path in self.video_folder_paths],
            'property_types': self.property_types.to_json_data(),
        }
        with open(self.file_path.path, 'w') as file:
            json.dump(json_info, file, indent=2)

    def save_video(self, video: Video):
        """ Save one video object to database folder.
        :param video: video to save.
        :return: 1 if effectively saved, else 0.
        """
        if video.updated:
            db_video_path = AbsolutePath.new_file_path(self.folder_path, video.video_id, self.FILE_EXTENSION)
            with open(db_video_path.path, 'w') as file:
                json.dump(video.to_json_data(), file, indent=2)
            video.updated = False
            return 1
        return 0

    def save(self):
        n_saved = 0
        with Profiler(exit_message='Database saved:'):
            self.save_database_file()
            for video in self.videos():
                n_saved += self.save_video(video)
        print(n_saved, 'videos saved.')


class Databases(object):
    __databases__ = {}  # type: dict{AbsolutePath, Database}

    @staticmethod
    def get(db_folder_name, video_folder_names=(), reset_paths=False):
        db_folder_path = AbsolutePath.ensure(db_folder_name)
        if db_folder_path in Databases.__databases__:
            database = Databases.__databases__[db_folder_path]
            if reset_path:
                database.reset_path(video_folder_names)
            return database
        new_database = Database(db_folder_name, video_folder_names, reset_paths=reset_paths)
        Databases.__databases__[new_database.folder_path] = new_database
        return new_database
