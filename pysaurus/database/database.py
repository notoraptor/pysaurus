import concurrent.futures
import functools
import os
import traceback
import ujson as json

from pysaurus.backend import pyav
from pysaurus.database import notifications
from pysaurus.database.notifier import Notifier
from pysaurus.database.property import PropertyTypeDict, PropertyDict
from pysaurus.database.report import DatabaseReport, DiskReport
from pysaurus.database.video_set import VideoSet
from pysaurus.utils import common
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.profiling import Profiler
from pysaurus.video.new_video import NewVideo
from pysaurus.video.video import Video


def load_videos_from_disk(notifier, job):
    """
    :param job:
    :return:
    :type notifier: Notifier
    :type job: (list[AbsolutePath], int)
    :rtype: (list[Video], list[(AbsolutePath, str)])
    """
    video_paths, initial_index = job
    loaded, errors = [], []
    count = 0
    next_index = initial_index
    for video_path in video_paths:
        count += 1
        try:
            new_video = NewVideo(video_path.path, video_id=next_index)
            loaded.append(new_video)
            next_index += 1
        except Exception:
            errors.append((video_path, traceback.format_exc()))
        if count % 25 == 0:
            notifier.notify(notifications.SteppingVideosLoading(count, len(video_paths), initial_index))
    if count % 25 != 0:
        notifier.notify(notifications.SteppingVideosLoading(count, len(video_paths), initial_index))
    return loaded, errors


class Database(VideoSet):
    __slots__ = ('__folder_path', '__file_path', '__video_folder_paths', '__property_types', '__notifier', '__max_id')
    VIDEO_ENTRY_EXTENSION = 'video.json'
    DB_FILE_EXTENSION = 'db.json'

    def __init__(self, db_folder_path: AbsolutePath, video_folder_names=(), reset_paths=False, load=True):
        super(Database, self).__init__()
        db_file_path = AbsolutePath.new_file_path(db_folder_path, db_folder_path.title, self.DB_FILE_EXTENSION)
        video_folder_paths = set()
        if db_file_path.exists():
            with open(db_file_path.path, 'rb') as db_file:
                json_info = json.load(db_file)
            assert json_info['name'] == db_folder_path.title
            if not reset_paths:
                video_folder_paths.update(AbsolutePath(path) for path in json_info['video_folders'])
            property_types = PropertyTypeDict.from_json_data(json_info['property_types'])
        else:
            property_types = PropertyTypeDict()
        video_folder_paths.update(AbsolutePath.ensure(path) for path in video_folder_names)
        self.__folder_path = db_folder_path
        self.__file_path = db_file_path
        self.__video_folder_paths = video_folder_paths
        self.__property_types = property_types  # type: PropertyTypeDict
        self.__max_id = 0
        self.__notifier = Notifier()
        if load:
            # If you need to configure something (e.g. notifier) before loading, create database with load == False,
            # configure what you want and load it later by calling database.load().
            self.load()

    name = property(lambda self: self.folder_path.title)
    folder_path = property(lambda self: self.__folder_path)
    file_path = property(lambda self: self.__file_path)
    video_folder_paths = property(lambda self: self.__video_folder_paths)
    property_types = property(lambda self: self.__property_types)
    notifier = property(lambda self: self.__notifier)

    def load(self):
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
        if self.__folder_path.exists():
            assert self.__folder_path.isdir()
        else:
            self.__folder_path.mkdir()

    def __load_videos_from_database(self, report: DatabaseReport):
        with Profiler(exit_message='Videos loaded from database:'):
            for file_name_from_db_folder in self.__folder_path.listdir():
                if common.has_extension(file_name_from_db_folder, self.VIDEO_ENTRY_EXTENSION):
                    report.n_files_checked += 1
                    db_video_path = AbsolutePath.join(self.__folder_path, file_name_from_db_folder)
                    try:
                        with open(db_video_path.path, 'rb') as db_video_file:
                            video = Video.from_json_data(json.load(db_video_file), self.__property_types)
                        if self.contains(video) and (
                                self.get_from_absolute_path(video.absolute_path).video_id != video.video_id):
                            report.removed.append(video)
                            self.__delete_entry(video)
                            continue
                        if not video.absolute_path.exists() or not video.absolute_path.isfile():
                            report.not_found.append(video)
                            self.__delete_entry(video)
                            continue
                        if video.absolute_path.get_dirname() not in self.__video_folder_paths:
                            report.removed.append(video)
                            self.__delete_entry(video)
                            continue
                        self.__max_id = max(self.__max_id, video.video_id)
                        self.add(video)
                        report.n_loaded += 1
                    except Exception:
                        db_video_path.delete()
                        report.errors.append((db_video_path, traceback.format_exc()))
        self.__notifier.notify(notifications.LoadedDatabase(report))

    def __load_videos_from_disk(self, report: DatabaseReport):
        with Profiler(exit_message='Videos collected from disk:'):
            for video_folder_path in sorted(self.__video_folder_paths):
                self.__collect_videos_from_folder(video_folder_path, report)
        self.__notifier.notify(notifications.ListedVideosFromDisk(report))
        count = report.count_from_disk()
        if count.collected:
            # Filter videos already loaded.
            video_paths_to_load = []
            for disk_report in report.disk.values():
                for video_path in disk_report.collected:
                    if self.contains_absolute_path(video_path) and (
                            video_path.get_date_modified() == self.get_from_absolute_path(video_path).date_modified):
                        disk_report.unloaded.append(video_path)
                    else:
                        video_paths_to_load.append(video_path)
            count_to_load = len(video_paths_to_load)
            if count.collected > count_to_load:
                self.__notifier.notify(notifications.VideosAlreadyLoadedFromDisk(report))
            if count_to_load:
                cpu_count = os.cpu_count()
                if cpu_count > count_to_load:
                    job_lengths = [1] * count_to_load
                else:
                    job_lengths = [count_to_load // cpu_count] * cpu_count
                    job_lengths[-1] += count_to_load % cpu_count
                assert sum(job_lengths) == count_to_load, (sum(job_lengths), count_to_load)
                next_id = self.__max_id + 1
                cursor = 0
                jobs = []
                for job_len in job_lengths:
                    jobs.append((video_paths_to_load[cursor:(cursor + job_len)], next_id))
                    cursor += job_len
                    next_id += job_len
                self.__max_id = next_id
                self.__notifier.notify(notifications.StartedVideosLoading())
                job_function = functools.partial(load_videos_from_disk, self.__notifier)
                with Profiler(exit_message='Finished to load %d videos:' % count.collected):
                    with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                        results = list(executor.map(job_function, jobs))
                for loaded, errors in results:
                    for new_video in loaded:  # type: NewVideo
                        disk_report = report.disk[new_video.absolute_path.get_dirname()]
                        if self.contains_absolute_path(new_video.absolute_path):
                            new_video.set_properties(self.get_from_absolute_path(new_video.absolute_path).properties)
                            disk_report.updated.append(new_video.absolute_path)
                        else:
                            new_video.set_properties(PropertyDict(self.__property_types))
                            disk_report.loaded.append(new_video.absolute_path)
                        self.add(new_video, update=True)
                    for path, traceback_string in errors:
                        disk_report = report.disk[path.get_dirname()]
                        disk_report.errors.append((path, traceback_string))
        self.__notifier.notify(notifications.FinishedVideosLoading(report))

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
        self.__notifier.notify(notifications.ListedVideosFromFolder(disk_report))

    def __delete_entry(self, video: Video, remove_video_definitively=False):
        entry_path = AbsolutePath.new_file_path(self.__folder_path, video.video_id, self.VIDEO_ENTRY_EXTENSION)
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
                                if (video.absolute_path.get_dirname() not in self.__video_folder_paths
                                    or not video.absolute_path.exists() or not video.absolute_path.isfile())]:
            self.__delete_entry(video_to_remove)

    def reset_paths(self, video_folder_names=()):
        database_report = DatabaseReport()
        self.__video_folder_paths.clear()
        self.__video_folder_paths.update(AbsolutePath.ensure(path) for path in video_folder_names)
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
                    video.set_thumbnail(pyav.create_thumbnail(video, self.__folder_path, video.video_id))

    def save_database_file(self):
        self.__ensure_database_folder()
        json_info = {
            'name': self.name,
            'video_folders': [str(path) for path in self.__video_folder_paths],
            'property_types': self.__property_types.to_json_data(),
        }
        with open(self.__file_path.path, 'w') as file:
            json.dump(json_info, file, indent=2)

    def save_video(self, video: Video):
        """ Save one video object to database folder.
        :param video: video to save.
        :return: 1 if effectively saved, else 0.
        """
        if video.updated:
            db_video_path = AbsolutePath.new_file_path(self.__folder_path, video.video_id, self.VIDEO_ENTRY_EXTENSION)
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
