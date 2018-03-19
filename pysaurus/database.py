import ujson as json
from datetime import datetime
from collections import namedtuple

from pysaurus.new_video import NewVideo
from pysaurus.property import PropertyTypeDict, PropertyDict
from pysaurus.utils import strings
from pysaurus.utils.symbols import is_valid_video_filename
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.video import Video
from pysaurus.utils.profiling import Profiling

DB_FILE_EXTENSION = 'json'
DB_FILE_DOT_EXTENSION = '.%s' % DB_FILE_EXTENSION

DatabaseLoadingResults = namedtuple('DatabaseLoadingResults', ('skipped', 'errors', 'not_found', 'n_loaded'))
VideoLoadingResults = namedtuple('VideoLoadingResults', ('skipped', 'errors', 'updated', 'n_loaded'))


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
        self.__load()

    name = property(lambda self: self.folder_path.title)

    def __load_videos_from_database(self):
        db_file_names_skipped = []
        db_video_paths_with_errors = []
        videos_not_found = []
        nb_videos_loaded = 0
        print('Loading videos from database.')
        for file_name_from_db_folder in self.folder_path.listdir():
            if file_name_from_db_folder != self.file_path.basename:
                if file_name_from_db_folder.endswith(DB_FILE_DOT_EXTENSION):
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
                        assert video.absolute_path_hash == db_video_path.title, "Invalid hash."
                        if video.absolute_path.exists() and video.absolute_path.isfile():
                            self.videos[video.path] = video
                            nb_videos_loaded += 1
                        else:
                            videos_not_found.append(video)
                    except Exception as e:
                        db_video_paths_with_errors.append((db_video_path, e))
                        print(db_video_path, type(e), e)
                else:
                    db_file_names_skipped.append(file_name_from_db_folder)
        print('Loaded', nb_videos_loaded, 'videos from database.')
        print('Skipped', len(db_file_names_skipped), 'invalid video file names from database.')
        print('Skipped', len(videos_not_found), 'videos not found on disk.')
        print('Skipped', len(db_video_paths_with_errors), 'videos with loading errors from database.')
        return DatabaseLoadingResults(
            skipped=db_file_names_skipped,
            errors=db_video_paths_with_errors,
            not_found=videos_not_found,
            n_loaded=nb_videos_loaded
        )

    def __load_videos_from_disk(self):
        file_names_skipped = []
        video_paths_updated = []
        video_paths_with_errors = []
        nb_videos_added = 0
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
                            new_video = NewVideo(video_path.path)
                            if video_path.path in self.videos:
                                new_video.set_properties(self.videos[video_path.path].properties)
                                video_paths_updated.append(video_path)
                            else:
                                new_video.set_properties(PropertyDict(self.property_types))
                                nb_videos_added += 1
                            self.videos[new_video.path] = new_video
                        except Exception as e:
                            video_paths_with_errors.append((video_path, e))
                            print(e)
                else:
                    print('here', video_file_name)
                    file_names_skipped.append(video_file_name)
                nb_files_checked += 1
                if nb_files_checked % 25 == 0:
                    print(nb_files_checked, 'files read.')
        time_end = datetime.now()
        print('Read', nb_files_checked, 'files.')
        print('Loaded', nb_videos_added, 'videos from disk.')
        print('Skipped', len(file_names_skipped), 'invalid video file names from disk.')
        print('Updated', len(video_paths_updated), 'videos from disk.')
        print('Skipped', len(video_paths_with_errors), 'videos with loading errors from disk.')
        print('Took', Profiling(time_start, time_end))
        return VideoLoadingResults(
            skipped=file_names_skipped,
            errors=video_paths_with_errors,
            updated=video_paths_updated,
            n_loaded=nb_videos_added
        )

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
                db_video_path = AbsolutePath.new_file_path(self.folder_path, video.absolute_path_hash,
                                                           DB_FILE_EXTENSION)
                with open(db_video_path.path, 'w') as file:
                    json.dump(video.to_json_data(), file, indent=2)
        time_end = datetime.now()
        print('Database saved in', Profiling(time_start, time_end))
