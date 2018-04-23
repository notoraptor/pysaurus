import codecs
import concurrent.futures
import functools
import os
import sys
import textwrap
import traceback
import ujson as json
import subprocess

from pysaurus.backend import pyav
from pysaurus.database import notifications
from pysaurus.database.notifier import Notifier
from pysaurus.database.property import PropertyTypeDict, PropertyDict
from pysaurus.database.report import DatabaseReport, DiskReport
from pysaurus.database.video_set import VideoSet
from pysaurus.utils import common
from pysaurus.utils import duration
from pysaurus.utils import strings
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.profiling import Profiler
from pysaurus.video.new_video import NewVideo
from pysaurus.video.video import Video


def load_videos_from_disk(folder_path, notifier, job):
    """
    :param job:
    :return:
    :type folder_path: AbsolutePath
    :type notifier: Notifier
    :type job: (list[AbsolutePath], int)
    :rtype: (list[Video], list[(AbsolutePath, str)])
    """
    video_paths, initial_index = job
    next_index = initial_index
    loaded, errors, json_errors = [], [], []
    errors_dict, warning_dict, short_to_long = {}, {}, {}
    ignored_set = set()
    json_lines = []

    list_file_path = AbsolutePath.new_file_path(folder_path, initial_index, 'list.txt')
    with open(list_file_path.path, 'w') as list_file:
        for path in video_paths:
            short_path = common.get_convenient_os_path(path.path)
            short_to_long[short_path] = path
            print(short_path, file=list_file)

    ##
    videoraptor_path = 'C:\\donnees\\programmation\\git\\videoraptor\\.local\\videoraptor.exe'
    command = [videoraptor_path, list_file_path.path]
    p = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True, bufsize=1)
    while True:
        # Thanks to (2018/04/22): https://www.endpoint.com/blog/2015/01/28/getting-realtime-output-using-python
        line = p.stdout.readline().strip()
        if line:
            if line.startswith('#FINISHED'):
                count = int(line[len('#FINISHED '):])
                notifier.notify(notifications.SteppingVideosLoading(count, len(video_paths), initial_index))
            elif line.startswith('#IGNORED'):
                ignored_set.add(line[len('#IGNORED '):])
            elif line.startswith('#LOADED'):
                count = int(line[len('#LOADED '):])
                notifier.notify(notifications.SteppingVideosLoading(count, len(video_paths), initial_index))
            elif line.startswith('#VIDEO_ERROR'):
                split_pos = line.index(']')
                video_filename = line[len('#VIDEO_ERROR['):split_pos]
                error_message = line[(split_pos + 1):]
                errors_dict.setdefault(video_filename, []).append(error_message)
            elif line.startswith('#VIDEO_WARNING'):
                split_pos = line.index(']')
                video_filename = line[len('#VIDEO_WARNING['):split_pos]
                warning_message = line[(split_pos + 1):]
                warning_dict.setdefault(video_filename, []).append(warning_message)
            elif line[0] != '#':
                json_lines.append(line)
        if p.poll() is not None:
            break

    std_out, std_err = p.communicate()
    list_file_path.delete()
    assert not std_out, std_out
    assert not std_err, std_err

    for line in json_lines:
        try:
            vdict = json.loads(line)
        except ValueError as exception:
            json_errors.append((line, exception))
        else:
            if vdict[strings.FILENAME] in short_to_long:
                short_name = vdict[strings.FILENAME]
                video_absolute_path = short_to_long.pop(short_name)
                movie_title = vdict.get(strings.TITLE, None)
                if movie_title:
                    movie_title = codecs.decode(movie_title, 'hex').decode()
                numerator, denominator = None, None
                frame_rate_pieces = vdict[strings.FRAME_RATE].split('/')
                if len(frame_rate_pieces) == 2:
                    numerator, denominator = int(frame_rate_pieces[0]), int(frame_rate_pieces[1])
                vdict[strings.FRAME_RATE] = numerator / denominator if numerator and denominator else None
                vdict[strings.DURATION] = vdict[strings.DURATION] * 1000000 / vdict[strings.DURATION_TIME_BASE]
                try:
                    new_video = Video()
                    new_video.update(vdict)
                    new_video.absolute_path = video_absolute_path
                    new_video.video_id = next_index
                    new_video.movie_title = movie_title
                    new_video.duration_unit = duration.MICROSECONDS
                    new_video.updated = True
                    if short_name in warning_dict:
                        new_video.suspect = warning_dict.pop(short_name)
                    new_video.validate()
                    loaded.append(new_video)
                    next_index += 1
                except AssertionError:
                    errors.append((video_absolute_path, traceback.format_exc()))

    json_errors_to_remove = set()
    if short_to_long:
        for short_name, video_path in short_to_long.items():
            messages = []
            if short_name in ignored_set:
                messages.append('Ignored')
                ignored_set.remove(short_name)
            if short_name in warning_dict:
                messages += warning_dict.pop(short_name)
            if short_name in errors_dict:
                messages += errors_dict.pop(short_name)
            for index, (line, exception) in enumerate(json_errors):
                if short_name in line:
                    messages.append('JSON Error ' + line)
                    messages.append(traceback.format_tb(exception.__traceback__))
                    json_errors_to_remove.add(index)
            if not messages:
                messages.append('Not loaded')
                print('NOT LOADED', video_path)
            errors.append((video_path, '\r\n'.join(messages)))
    assert not ignored_set, len(ignored_set)
    assert not errors_dict, len(errors_dict)
    assert not warning_dict, len(warning_dict)
    if len(json_errors_to_remove) != len(json_errors):
        for line, exception in json_errors:
            print('ERROR', line, file=sys.stderr)
            print('ERROR', traceback.format_tb(exception.__traceback__), file=sys.stderr)
            print('ERROR', exception, file=sys.stderr)
        raise AssertionError((len(json_errors_to_remove), len(json_errors)))

    notifier.notify(notifications.SteppingVideosLoading(len(video_paths), len(video_paths), initial_index))
    return loaded, errors


class Database(VideoSet):
    __slots__ = ('__folder_path', '__file_path', '__video_folder_paths', '__property_types', '__notifier', '__max_id')
    VIDEO_ENTRY_EXTENSION = 'video.json'
    DB_FILE_EXTENSION = 'db.json'
    LIST_EXTENSION = 'list.txt'
    RESULT_EXTENSION = 'list.json'

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
                job_function = functools.partial(load_videos_from_disk, self.folder_path, self.notifier)
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
                    for video_path, traceback_string in errors:
                        disk_report = report.disk[video_path.get_dirname()]
                        disk_report.errors.append((video_path, traceback_string))
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
        self.notifier.notify(notifications.StartedDatabaseSaving())
        with Profiler(exit_message='Database saved:'):
            self.save_database_file()
            self.notifier.notify(notifications.SavedDatabaseFile())
            for video in self.videos():
                n_saved += self.save_video(video)
                if n_saved and n_saved % 200 == 0:
                    self.notifier.notify(notifications.SteppingDatabaseSaving(n_saved, self.size()))
        self.notifier.notify(notifications.FinishedDatabaseSaving(self.size()))
