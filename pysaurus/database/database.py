import ujson as json

from pysaurus.backend import pyav
from pysaurus.database import notifications
from pysaurus.database.notifier import Notifier
from pysaurus.database.property import PropertyTypeDict, PropertyDict
from pysaurus.database.report import DatabaseReport, DiskReport
from pysaurus.database.video_set import VideoSet
from pysaurus.utils import common
from pysaurus.utils import exceptions
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.profiling import Profiler
from pysaurus.video.new_video import NewVideo
from pysaurus.video.video import Video


class Database(VideoSet):
    __cache__ = {}  # type: dict{AbsolutePath, Database}
    __slots__ = {'folder_path', 'file_path', 'video_folder_paths', 'property_types', 'NOTIFIER', '__max_id'}
    VIDEO_ENTRY_EXTENSION = 'video.json'
    DB_FILE_EXTENSION = 'db.json'

    def __new__(cls, db_folder_path: AbsolutePath, video_folder_names=(), reset_paths=False):
        if db_folder_path in cls.__cache__:
            database = cls.__cache__[db_folder_path]
            if reset_paths:
                database.reset_paths(video_folder_names)
            return database
        return object.__new__(cls)

    def __init__(self, db_folder_path: AbsolutePath, video_folder_names=(), reset_paths=False):
        if db_folder_path in self.__cache__:
            return
        super(Database, self).__init__()
        db_file_path = AbsolutePath.new_file_path(db_folder_path, db_folder_path.title, self.DB_FILE_EXTENSION)
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
        self.NOTIFIER = Notifier()
        self.__load()
        self.__cache__[self.folder_path] = self

    name = property(lambda self: self.folder_path.title)

    def __load(self):
        report = DatabaseReport()
        self.__ensure_database_folder()
        try:
            self.__load_videos_from_database(report)
            self.__load_videos_from_disk(report)
            # self.check_thumbnails()
        finally:
            self.save()
        return report

    def __ensure_database_folder(self):
        if self.folder_path.exists():
            assert self.folder_path.isdir()
        else:
            self.folder_path.mkdir()

    def __load_videos_from_database(self, report: DatabaseReport):
        for file_name_from_db_folder in self.folder_path.listdir():
            if common.has_extension(file_name_from_db_folder, self.VIDEO_ENTRY_EXTENSION):
                report.n_files_checked += 1
                db_video_path = AbsolutePath.join(self.folder_path, file_name_from_db_folder)
                try:
                    with open(db_video_path.path, 'rb') as db_video_file:
                        json_info = json.load(db_video_file)
                    video = Video.from_json_data(json_info, self.property_types)
                    if self.contains(video):
                        raise exceptions.DuplicateEntryException()
                    if not video.absolute_path.exists() or not video.absolute_path.isfile():
                        report.not_found.append(video)
                        self.__delete_entry(video)
                        continue
                    if video.absolute_path.get_dirname() not in self.video_folder_paths:
                        report.removed.append(video)
                        self.__delete_entry(video)
                        continue
                    self.__max_id = max(self.__max_id, video.video_id)
                    self.add(video)
                    report.n_loaded += 1
                except Exception as e:
                    db_video_path.delete()
                    report.errors.append((db_video_path, e))
        self.NOTIFIER.notify(notifications.LoadedDatabase(report))

    def __load_videos_from_disk(self, report: DatabaseReport):
        with Profiler(exit_message='Videos collected from disk:'):
            for video_folder_path in sorted(self.video_folder_paths):
                self.__collect_videos_from_folder(video_folder_path, report)
        self.NOTIFIER.notify(notifications.ListedVideosFromDisk(report))
        count = report.count_from_disk()
        if count.collected:
            n_read = 0
            self.NOTIFIER.notify(notifications.StartedVideosLoading())
            with Profiler(exit_message='Finished to load %d videos:' % count.collected):
                for disk_report in report.disk.values():  # type: DiskReport
                    for video_path in disk_report.collected:
                        n_read += 1
                        try:
                            self.__load_video(video_path, disk_report)
                        except Exception as exception:
                            disk_report.errors.append((video_path, exception))
                        if n_read % 25 == 0:
                            self.NOTIFIER.notify(notifications.SteppingVideosLoading(n_read, count.collected))
        self.NOTIFIER.notify(notifications.FinishedVideosLoading(report))

    def __load_video(self, video_path: AbsolutePath, disk_report: DiskReport):
        """ Load one video from disk to the database.
        :param video_path: path to video to load.
        :return: a LoadStatus value.
        """
        if self.contains_absolute_path(video_path) and (
                video_path.get_date_modified() == self.get_from_absolute_path(video_path).date_modified):
            disk_report.unloaded.append(video_path)
        else:
            new_id = self.__max_id + 1
            new_video = NewVideo(video_path.path, video_id=new_id)
            if self.contains_absolute_path(video_path):
                new_video.set_properties(self.get_from_absolute_path(video_path).properties)
                disk_report.updated.append(video_path)
            else:
                new_video.set_properties(PropertyDict(self.property_types))
                disk_report.loaded.append(video_path)
            self.add(new_video)
            self.__max_id = new_id

    def __collect_videos_from_folder(self, video_folder_path: AbsolutePath, report: DatabaseReport):
        disk_report = DiskReport(video_folder_path)
        for file_name in video_folder_path.listdir():
            file_path = AbsolutePath.join(video_folder_path, file_name)
            if file_path.isdir():
                self.__collect_videos_from_folder(file_path, report)
            elif file_path.isfile() and common.is_valid_video_filename(file_name):
                disk_report.collected.append(file_path)
            else:
                disk_report.ignored.append(file_path)
        report.disk[disk_report.folder_path] = disk_report
        self.NOTIFIER.notify(notifications.ListedVideosFromFolder(disk_report))

    def __delete_entry(self, video: Video, remove_video_definitively=False):
        entry_path = AbsolutePath.new_file_path(self.folder_path, video.video_id, self.VIDEO_ENTRY_EXTENSION)
        assert entry_path.exists() and entry_path.isfile()
        entry_path.delete()
        video.delete_thumbnail()
        assert not entry_path.exists()
        if self.contains_absolute_path(video.absolute_path):
            self.remove_from_absolute_path(video.absolute_path)
        if remove_video_definitively:
            video.absolute_path.delete()
            assert not video.absolute_path.exists()

    def clean_database(self):
        for video_to_remove in [video for video in self.videos()
                                if (video.absolute_path.get_dirname() not in self.video_folder_paths
                                    or not video.absolute_path.exists() or not video.absolute_path.isfile())]:
            self.__delete_entry(video_to_remove)

    def reset_paths(self, video_folder_names=()):
        database_report = DatabaseReport()
        self.video_folder_paths.clear()
        self.video_folder_paths.update(AbsolutePath.ensure(path) for path in video_folder_names)
        try:
            self.clean_database()
            self.__load_videos_from_disk(database_report)
            # self.check_thumbnails()
        finally:
            self.save()
        return database_report

    def check_thumbnails(self):
        with Profiler(exit_message='Finished checking thumbnails:'):
            for index, video in enumerate(self.videos()):  # type: (int, Video)
                if not video.has_valid_thumbnail():
                    print('(%d) Creating thumbnail:' % (index + 1), video.absolute_path)
                    video.set_thumbnail(pyav.create_thumbnail(video, self.folder_path, video.video_id))

    def save_database_file(self):
        self.__ensure_database_folder()
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
            db_video_path = AbsolutePath.new_file_path(self.folder_path, video.video_id, self.VIDEO_ENTRY_EXTENSION)
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
