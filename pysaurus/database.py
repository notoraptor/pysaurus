import ujson as json
from io import StringIO

from pysaurus.new_video import NewVideo
from pysaurus.property import PropertyTypeDict, PropertyDict
from pysaurus.utils import exceptions, ffmpeg_backend
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.profiling import Profiler
from pysaurus.utils.symbols import is_valid_video_filename
from pysaurus.video import Video

DB_FILE_EXTENSION = 'json'
DB_FILE_DOT_EXTENSION = '.%s' % DB_FILE_EXTENSION


class Report(object):
    __slots__ = ('db_n_files_checked', 'db_files_skipped', 'db_errors', 'db_not_found', 'db_n_loaded', 'db_n_saved',
                 'disk_n_files_checked', 'disk_files_skipped', 'disk_errors', 'disk_updated', 'disk_n_loaded')

    def __init__(self):
        self.db_files_skipped = []
        self.db_errors = []
        self.db_not_found = []
        self.db_n_files_checked = 0
        self.db_n_loaded = 0
        self.db_n_saved = 0
        self.disk_files_skipped = []
        self.disk_errors = []
        self.disk_updated = []
        self.disk_n_files_checked = 0
        self.disk_n_loaded = 0

    def __str__(self):
        string_pieces = []
        longest_printed_name_length = 0
        string_version = StringIO()
        for name in self.__slots__:
            value = getattr(self, name)
            value_length = value if isinstance(value, int) else len(value)
            if value_length:
                string_pieces.append((name, value_length))
                longest_printed_name_length = max(longest_printed_name_length, len(name))
        print(self.__class__.__name__, file=string_version, end='')
        if longest_printed_name_length:
            string_format = '\t{:<%d}:\t{}' % (longest_printed_name_length + 1)
            print(' {', file=string_version)
            for name, value_length in string_pieces:
                print(string_format.format(name, value_length), file=string_version)
            print('}', file=string_version)
        else:
            print('{}', file=string_version)
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
        return self.__videos[absolute_path]

    def get_from_path_string(self, path_string: str):
        return self.__videos[AbsolutePath(path_string)]

    def videos(self):
        return self.__videos.values()


class Database(VideoSet):
    __slots__ = {'folder_path', 'file_path', 'video_folder_paths', 'property_types', '__max_id'}

    def __init__(self, db_folder_name=None, video_folder_names=()):
        super(Database, self).__init__()
        db_folder_path = AbsolutePath(db_folder_name)
        db_file_path = AbsolutePath.new_file_path(db_folder_path, db_folder_path.title, DB_FILE_EXTENSION)
        if db_file_path.exists():
            with open(db_file_path.path, 'rb') as db_file:
                json_info = json.load(db_file)
            assert json_info['name'] == db_folder_path.title
            video_folder_paths = {AbsolutePath(path) for path in json_info['video_folders']}
            property_types = PropertyTypeDict.from_json_data(json_info['property_types'])
            video_folder_paths.update(AbsolutePath(path) for path in video_folder_names)
        else:
            video_folder_paths = {AbsolutePath(path) for path in video_folder_names}
            property_types = PropertyTypeDict()
        self.folder_path = db_folder_path
        self.file_path = db_file_path
        self.video_folder_paths = video_folder_paths
        self.property_types = property_types  # type: PropertyTypeDict
        self.__max_id = 0
        self.__load()
        self.check_thumbnails()

    name = property(lambda self: self.folder_path.title)

    def __load_videos_from_database(self, report: Report = None):
        if report is None:
            report = Report()
        for file_name_from_db_folder in self.folder_path.listdir():
            if file_name_from_db_folder != self.file_path.basename:
                report.db_n_files_checked += 1
                if not file_name_from_db_folder.endswith(DB_FILE_DOT_EXTENSION):
                    report.db_files_skipped.append(file_name_from_db_folder)
                    continue
                db_video_path = AbsolutePath.join(self.folder_path, file_name_from_db_folder)
                try:
                    with open(db_video_path.path, 'rb') as db_video_file:
                        json_info = json.load(db_video_file)
                    video = Video.from_json_data(json_info, self.property_types)
                    if video.video_id is None:
                        raise exceptions.VideoIdException()
                    if self.contains(video):
                        raise exceptions.DuplicateEntryException()
                    if not video.absolute_path.exists() or not video.absolute_path.isfile():
                        report.db_not_found.append(video)
                        db_video_path.delete()
                        continue
                    self.__max_id = max(self.__max_id, video.video_id)
                    self.add(video)
                    video.updated = False
                    report.db_n_loaded += 1
                except Exception as e:
                    db_video_path.delete()
                    report.db_errors.append((db_video_path, e))
        return report

    def __load_video_from_folder(self, video_folder_path, report: Report = None, show_progression=True):
        """
        :type report: LoadReport
        """
        video_folder_path = AbsolutePath.ensure(video_folder_path)
        if report is None:
            report = Report()
        if show_progression:
            print('Loading videos from folder', video_folder_path)
        for video_file_name in video_folder_path.listdir():
            report.disk_n_files_checked += 1
            if show_progression and report.disk_n_files_checked % 25 == 0:
                print(report.disk_n_files_checked, 'files checked.')
            if not is_valid_video_filename(video_file_name):
                report.disk_files_skipped.append(video_file_name)
                continue
            video_path = AbsolutePath.join(video_folder_path, video_file_name)
            if self.contains_absolute_path(video_path) and (
                    video_path.get_date_modified() == self.get_from_absolute_path(video_path).date_modified):
                continue
            try:
                new_id = self.__max_id + 1
                new_video = NewVideo(video_path.path, video_id=new_id)
                if self.contains_absolute_path(video_path):
                    new_video.set_properties(self.get_from_absolute_path(video_path).properties)
                    report.disk_updated.append(video_path)
                else:
                    new_video.set_properties(PropertyDict(self.property_types))
                    report.disk_n_loaded += 1
                self.add(new_video)
                self.__max_id = new_id
            except Exception as e:
                report.disk_errors.append((video_path, e))
        return report

    def __load_videos_from_disk(self, report: Report = None, show_progression=True):
        if report is None:
            report = Report()
        for video_folder_path in self.video_folder_paths:
            self.__load_video_from_folder(video_folder_path, report, show_progression)
        return report

    def __load(self):
        report = Report()
        with Profiler('Loading videos from database.', 'Videos loaded from database:'):
            self.__load_videos_from_database(report=report)
        with Profiler('Loading videos from disk.', 'Videos loaded from disk:'):
            self.__load_videos_from_disk(report=report)
        print(report)

    def check_thumbnails(self):
        for video in self.videos():  # type: Video
            if not video.has_valid_thumbnail():
                print('Generating video for', video.absolute_path)
                video.set_thumbnail(ffmpeg_backend.create_thumbnail(video, self.folder_path))

    def save(self):
        report = Report()
        with Profiler('Saving database.', 'Database saved:'):
            if not self.folder_path.exists():
                self.folder_path.mkdir()
            else:
                assert self.folder_path.isdir()
            json_info = {
                'name': self.name,
                'video_folders': [str(path) for path in self.video_folder_paths],
                'property_types': self.property_types.to_json_data(),
            }
            with open(self.file_path.path, 'w') as file:
                json.dump(json_info, file, indent=2)
            for video in self.videos():
                if video.updated:
                    db_video_path = AbsolutePath.new_file_path(self.folder_path, video.video_id, DB_FILE_EXTENSION)
                    with open(db_video_path.path, 'w') as file:
                        json.dump(video.to_json_data(), file, indent=2)
                    report.db_n_saved += 1
        print(report)
