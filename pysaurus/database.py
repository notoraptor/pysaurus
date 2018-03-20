import ujson as json
from collections import namedtuple
from datetime import datetime

from pysaurus.new_video import NewVideo
from pysaurus.property import PropertyTypeDict, PropertyDict
from pysaurus.utils import strings
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.profiling import Profiling
from pysaurus.utils.symbols import is_valid_video_filename
from pysaurus.video import Video

DB_FILE_EXTENSION = 'json'
DB_FILE_DOT_EXTENSION = '.%s' % DB_FILE_EXTENSION

DatabaseLoadingResults = namedtuple('DatabaseLoadingResults', ('skipped', 'errors', 'not_found', 'n_loaded'))
VideoLoadingResults = namedtuple('VideoLoadingResults', ('skipped', 'errors', 'updated', 'n_loaded'))


class LoadReport(object):
    __slots__ = {'skipped', 'errors', 'updated', 'n_loaded', '__origin', '__update'}

    def __init__(self, origin_name='', update_name='updated'):
        if origin_name:
            origin_name = 'from %s' % origin_name
        self.__origin = origin_name
        self.__update = update_name
        self.skipped = []
        self.errors = []
        self.updated = []
        self.n_loaded = 0

    def __str__(self):
        return ('Load report%s (skipped = %d, errors = %d, %s = %d, loaded = %d)'
                % (self.__origin, len(self.skipped), len(self.errors),
                   self.__update, len(self.updated), self.n_loaded))


class Database(object):
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
        print('Loading videos from database.')
        for file_name_from_db_folder in self.folder_path.listdir():
            if file_name_from_db_folder != self.file_path.basename:
                if not file_name_from_db_folder.endswith(DB_FILE_DOT_EXTENSION):
                    report.skipped.append(file_name_from_db_folder)
                else:
                    db_video_path = AbsolutePath.join(self.folder_path, file_name_from_db_folder)
                    try:
                        with open(db_video_path.path, 'rb') as db_video_file:
                            json_info = json.load(db_video_file)
                        if json_info.get(strings.PROPERTIES, None) is not None:
                            json_info[strings.PROPERTIES] = PropertyDict.from_json_data(
                                json_info[strings.PROPERTIES], self.property_types)
                        else:
                            json_info[strings.PROPERTIES] = PropertyDict(self.property_types)
                        video = Video(**json_info)
                        assert video.video_id is not None, 'Invalid video ID.'
                        self.__max_id = max(self.__max_id, video.video_id)
                        if video.absolute_path.exists() and video.absolute_path.isfile():
                            self.videos[video.path] = video
                            report.n_loaded += 1
                        else:
                            report.updated.append(video)
                    except Exception as e:
                        report.errors.append((db_video_path, e))
                        print(db_video_path, type(e), e)
        print(report)
        return report

    def __load_videos_from_disk(self):
        report = LoadReport()
        print('Loading videos from disk.')
        nb_files_checked = 0
        time_start = datetime.now()
        for video_folder_path in self.video_folder_paths:
            for video_file_name in video_folder_path.listdir():
                if is_valid_video_filename(video_file_name):
                    video_path = AbsolutePath.join(video_folder_path, video_file_name)
                    if video_path.path not in self.videos or (
                            video_path.get_date_modified() > self.videos[video_path.path].date_modified):
                        try:
                            self.__max_id += 1
                            new_video = NewVideo(video_path.path, video_id=self.__max_id)
                            if video_path.path in self.videos:
                                new_video.set_properties(self.videos[video_path.path].properties)
                                report.updated.append(video_path)
                            else:
                                new_video.set_properties(PropertyDict(self.property_types))
                                report.n_loaded += 1
                            self.videos[new_video.path] = new_video
                        except Exception as e:
                            report.errors.append((video_path, e))
                            print(e)
                else:
                    report.skipped.append(video_file_name)
                nb_files_checked += 1
                if nb_files_checked % 25 == 0:
                    print(nb_files_checked, 'files read.')
        time_end = datetime.now()
        print('Checked', nb_files_checked, 'files.')
        print(report)
        print('Took', Profiling(time_start, time_end))
        return report

    def __load(self):
        self.__load_videos_from_database()
        self.__load_videos_from_disk()

    def save(self):
        print('Saving database.')
        time_start = datetime.now()
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
                db_video_path = AbsolutePath.new_file_path(self.folder_path, video.video_id, DB_FILE_EXTENSION)
                with open(db_video_path.path, 'w') as file:
                    json.dump(video.to_json_data(), file, indent=2)
        time_end = datetime.now()
        print('Database saved in', Profiling(time_start, time_end))
