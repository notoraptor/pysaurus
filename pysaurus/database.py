import ujson as json

from pysaurus.new_video import NewVideo
from pysaurus.property import PropertyTypeDict, PropertyDict
from pysaurus.utils import exceptions
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.profiling import Profiler
from pysaurus.utils.symbols import is_valid_video_filename
from pysaurus.video import Video

DB_FILE_EXTENSION = 'json'
DB_FILE_DOT_EXTENSION = '.%s' % DB_FILE_EXTENSION


class LoadReport(object):
    __slots__ = {'skipped', 'errors', 'updated', 'n_loaded', 'n_checked', '__origin', '__update'}

    def __init__(self, origin_name='', update_name='updated'):
        self.__origin = ('from %s' % origin_name) if origin_name else ''
        self.__update = update_name
        self.skipped = []
        self.errors = []
        self.updated = []
        self.n_loaded = 0
        self.n_checked = 0

    def __str__(self):
        return ('Load report%s (checked = %d, loaded = %d, skipped = %d, errors = %d, %s = %d)'
                % (self.__origin, self.n_checked, self.n_loaded, len(self.skipped), len(self.errors),
                   self.__update, len(self.updated)))


class Database(object):
    __slots__ = {'folder_path', 'file_path', 'video_folder_paths', 'property_types', 'videos', '__max_id'}

    def __init__(self, db_folder_name=None, video_folder_names=()):
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
        self.videos = {}  # type: dict{str, Video}
        self.__max_id = 0
        self.__load()

    name = property(lambda self: self.folder_path.title)

    def __load_videos_from_database(self):
        report = LoadReport(update_name='not_found')
        for file_name_from_db_folder in self.folder_path.listdir():
            report.n_checked += 1
            if file_name_from_db_folder != self.file_path.basename:
                if not file_name_from_db_folder.endswith(DB_FILE_DOT_EXTENSION):
                    report.skipped.append(file_name_from_db_folder)
                    continue
                db_video_path = AbsolutePath.join(self.folder_path, file_name_from_db_folder)
                try:
                    with open(db_video_path.path, 'rb') as db_video_file:
                        json_info = json.load(db_video_file)
                    video = Video.from_json_data(json_info, self.property_types)
                    if video.video_id is None:
                        raise exceptions.VideoIdException()
                    if video.path in self.videos:
                        raise exceptions.DuplicateEntryException()
                    if not video.absolute_path.exists() or not video.absolute_path.isfile():
                        report.updated.append(video)
                        db_video_path.delete()
                        continue
                    self.__max_id = max(self.__max_id, video.video_id)
                    self.videos[video.path] = video
                    video.updated = False
                    report.n_loaded += 1
                except Exception as e:
                    db_video_path.delete()
                    report.errors.append((db_video_path, e))
        return report

    def __load_video_from_folder(self, video_folder_path, report=None, show_progression=True):
        """
        :type report: LoadReport
        """
        video_folder_path = AbsolutePath.ensure(video_folder_path)
        if report is None:
            report = LoadReport()
        if show_progression:
            print('Loading videos from folder', video_folder_path)
        for video_file_name in video_folder_path.listdir():
            report.n_checked += 1
            if show_progression and report.n_checked % 25 == 0:
                print(report.n_checked, 'files checked.')
            if not is_valid_video_filename(video_file_name):
                report.skipped.append(video_file_name)
                continue
            video_path = AbsolutePath.join(video_folder_path, video_file_name)
            if video_path.path in self.videos and (
                    video_path.get_date_modified() == self.videos[video_path.path].date_modified):
                continue
            try:
                new_id = self.__max_id + 1
                new_video = NewVideo(video_path.path, video_id=new_id)
                if video_path.path in self.videos:
                    new_video.set_properties(self.videos[video_path.path].properties)
                    report.updated.append(video_path)
                else:
                    new_video.set_properties(PropertyDict(self.property_types))
                    report.n_loaded += 1
                self.videos[new_video.path] = new_video
                self.__max_id = new_id
            except Exception as e:
                report.errors.append((video_path, e))
        return report

    def __load_videos_from_disk(self, show_progression=True):
        report = LoadReport()
        for video_folder_path in self.video_folder_paths:
            self.__load_video_from_folder(video_folder_path, report, show_progression)
        return report

    def __load(self):
        with Profiler('Loading videos from database.', 'Videos loaded from database:'):
            report = self.__load_videos_from_database()
        print(report)
        with Profiler('Loading videos from disk.', 'Videos loaded from disk:'):
            report = self.__load_videos_from_disk()
        print(report)

    def save(self):
        report = LoadReport()
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
            for video in self.videos.values():
                if video.updated:
                    report.n_checked += 1
                    db_video_path = AbsolutePath.new_file_path(self.folder_path, video.video_id, DB_FILE_EXTENSION)
                    with open(db_video_path.path, 'w') as file:
                        json.dump(video.to_json_data(), file, indent=2)
        print(report)
