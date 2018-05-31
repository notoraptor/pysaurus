import codecs
import concurrent.futures
import functools
import os
import subprocess
import sys
import traceback
import ujson as json

from pysaurus.database import notifications, videoraptor
from pysaurus.database.notifier import Notifier
from pysaurus.database.property import PropertyTypeDict, PropertyDict
from pysaurus.database.report import DatabaseReport, DiskReport
from pysaurus.database.video import Video
from pysaurus.database.video_set import VideoSet
from pysaurus.utils import common
from pysaurus.utils import duration
from pysaurus.utils import strings
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.profiling import Profiler

VIDEO_RAPTOR = 'C:\\donnees\\programmation\\git\\videoraptor\\.local\\videoraptor.exe'

VIDEO_ENTRY_EXTENSION = 'video.json'
LIST_EXTENSION = 'list.txt'
DB_FILE_TITLE = 'database'
DB_FILE_EXTENSION = 'db.json'
THUMBNAIL_EXTENSION = 'png'


class Job(object):
    __slots__ = ('tasks', 'identifier', 'errors', 'success', 'global_errors')

    def __init__(self, tasks, identifier):
        self.identifier = identifier
        self.tasks = tasks
        self.errors = []
        self.success = []
        self.global_errors = []


class Videoraptor(object):
    ERROR = '#ERROR'
    FINISHED = '#FINISHED'
    IGNORED = '#IGNORED'
    LOADED = '#LOADED'
    MESSAGE = '#MESSAGE'
    USAGE = '#USAGE'
    VIDEO_ERROR = '#VIDEO_ERROR'
    VIDEO_WARNING = '#VIDEO_WARNING'

    __prefixes__ = (ERROR, FINISHED, IGNORED, LOADED, MESSAGE, USAGE, VIDEO_ERROR, VIDEO_WARNING)

    @classmethod
    def get_prefix(cls, line):
        for prefix in cls.__prefixes__:
            if line.startswith(prefix):
                return prefix
        return None


def load_videos_from_disk(folder_path, notifier, job_details):
    """
        :type folder_path: AbsolutePath
        :type notifier: Notifier
        :type job_details: list
        :rtype: (list[Video], list[(AbsolutePath, str)])
    """

    # For real-time reading of subprocess output,
    # thanks to (2018/04/22): https://www.endpoint.com/blog/2015/01/28/getting-realtime-output-using-python

    print('Using videoraptor DLL')

    job = Job(job_details[0], job_details[1])
    next_index = job.identifier
    json_errors = []
    errors_dict, warning_dict, short_to_long = {}, {}, {}
    ignored_set = set()
    short_paths = []

    complete_output = ''

    for path in job.tasks:
        short_path = common.get_convenient_os_path(path.path)
        short_to_long[short_path] = path
        short_paths.append(short_path)

    cursor = 0
    while True:
        result = videoraptor.run(short_paths, cursor)
        if not result:
            break
        output_string, len_consumed = result
        cursor += len_consumed
        complete_output += output_string
        if (cursor + 1) % 25 == 0:
            notifier.notify(notifications.SteppingVideosLoading(cursor + 1, len(job.tasks), job.identifier))

    for line in complete_output.splitlines():
        line = line.strip()
        if not line:
            continue

        prefix = Videoraptor.get_prefix(line)
        if prefix == Videoraptor.ERROR:
            job.global_errors.append(line[len(prefix + ' '):])
        elif prefix == Videoraptor.IGNORED:
            ignored_set.add(line[len(prefix + ' '):])
        elif prefix in (Videoraptor.VIDEO_ERROR, Videoraptor.VIDEO_WARNING):
            split_pos = line.index(']')
            video_filename = line[len(prefix + '['):split_pos]
            parsed_message = line[(split_pos + 1):]
            if prefix == Videoraptor.VIDEO_ERROR:
                errors_dict.setdefault(video_filename, []).append(parsed_message)
            else:
                warning_dict.setdefault(video_filename, []).append(parsed_message)
        elif line[0] == '#':
            continue

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
                    job.success.append(new_video)
                    next_index += 1
                except AssertionError:
                    job.errors.append((video_absolute_path, traceback.format_exc()))

    nb_json_errors_handled = 0
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
                    messages.extend(traceback.format_tb(exception.__traceback__))
                    nb_json_errors_handled += 1
            if not messages:
                messages.append('Not loaded')
                print('NOT LOADED', video_path)
            job.errors.append((video_path, '\r\n'.join(messages)))
    assert not ignored_set, len(ignored_set)
    assert not errors_dict, len(errors_dict)
    assert not warning_dict, len(warning_dict)
    if nb_json_errors_handled != len(json_errors):
        for line, exception in json_errors:
            print('ERROR', line, file=sys.stderr)
            print('ERROR', traceback.format_tb(exception.__traceback__), file=sys.stderr)
            print('ERROR', exception, file=sys.stderr)
        raise AssertionError((nb_json_errors_handled, len(json_errors)))

    notifier.notify(notifications.SteppingVideosLoading(len(job.tasks), len(job.tasks), job.identifier))
    return job


def generate_thumbnails(folder_path, notifier, job_details):
    """
        :type folder_path: AbsolutePath
        :type notifier: Notifier
        :type job_details: list
        :rtype: (list[Video], list[(AbsolutePath, str)])
    """
    tasks, job_id = job_details
    global_errors = []

    list_file_path = AbsolutePath.new_file_path(folder_path, job_id, LIST_EXTENSION)
    with open(list_file_path.path, 'w') as list_file:
        for video_path, video_index in tasks:
            short_path = common.get_convenient_os_path(video_path.path)
            print('%s\t%s\t%s' % (short_path, folder_path, video_index), file=list_file)

    command = [VIDEO_RAPTOR, list_file_path.path]
    p = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True, bufsize=1)
    while True:
        line = p.stdout.readline().strip()
        if line:
            prefix = Videoraptor.get_prefix(line)
            if prefix in (Videoraptor.FINISHED, Videoraptor.LOADED):
                count = int(line[len(prefix + ' '):])
                notifier.notify(notifications.SteppingThumbnailsGenerator(count, len(tasks), job_id))
            elif prefix not in (Videoraptor.MESSAGE, Videoraptor.VIDEO_WARNING):
                global_errors.append(line)
        if p.poll() is not None:
            break

    std_out, std_err = p.communicate()
    list_file_path.delete()
    assert not std_out, std_out
    assert not std_err, std_err

    notifier.notify(notifications.SteppingThumbnailsGenerator(len(tasks), len(tasks), job_id))
    return global_errors


class Database(VideoSet):
    __slots__ = ('__folder_path', '__file_path', '__video_folder_paths', '__property_types', '__notifier', '__max_id',
                 '__not_found', '__keep_invalid_entries')

    def __init__(self, db_folder, *, video_folders=(), keep_old_paths=True, load=True, keep_invalid_entries=True):
        super(Database, self).__init__()
        db_folder = AbsolutePath.ensure(db_folder)
        db_file_path = AbsolutePath.new_file_path(db_folder, DB_FILE_TITLE, DB_FILE_EXTENSION)
        video_folder_paths = set()
        not_found = set()
        if db_file_path.exists():
            with open(db_file_path.path, 'rb') as db_file:
                json_info = json.load(db_file)
            if keep_old_paths:
                video_folder_paths.update(AbsolutePath(path) for path in json_info['video_folders'])
            property_types = PropertyTypeDict.from_json_data(json_info['property_types'])
            not_found.update(json_info.get('not_found', ()))
        else:
            property_types = PropertyTypeDict()
        video_folder_paths.update(AbsolutePath.ensure(path) for path in video_folders)
        self.__folder_path = db_folder
        self.__file_path = db_file_path
        self.__video_folder_paths = video_folder_paths
        self.__property_types = property_types
        self.__max_id = 0
        self.__notifier = Notifier()
        self.__not_found = not_found
        self.__keep_invalid_entries = bool(keep_invalid_entries)
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
            self.ensure_thumbnails()
        finally:
            self.save()
        return report

    def __ensure_database_folder(self):
        if self.__folder_path.exists():
            assert self.__folder_path.isdir(), 'Expected a folder at path %s' % self.__folder_path
        else:
            self.__folder_path.mkdir()

    def __load_videos_from_database(self, report: DatabaseReport):
        with Profiler(exit_message='Videos loaded from database:'):
            for file_name_from_db_folder in self.__folder_path.listdir():
                if common.has_extension(file_name_from_db_folder, VIDEO_ENTRY_EXTENSION):
                    report.n_checked += 1
                    db_video_path = AbsolutePath.join(self.__folder_path, file_name_from_db_folder)
                    try:
                        with open(db_video_path.path, 'rb') as db_video_file:
                            video = Video.from_json_data(json.load(db_video_file), self.__property_types)
                        if not self.__keep_invalid_entries:
                            if not video.absolute_path.exists() or not video.absolute_path.isfile():
                                report.not_found.append(video)
                                self.__not_found.add(video.absolute_path.path)
                                self.__delete_entry(video)
                                continue
                        if video.absolute_path.get_dirname() not in self.__video_folder_paths or self.contains(video):
                            report.removed.append(video)
                            self.__delete_entry(video)
                            continue
                        self.__max_id = max(self.__max_id, video.video_id)
                        self.add(video)
                        report.n_loaded += 1
                    except ValueError:
                        db_video_path.delete()
                        report.errors.append((db_video_path, traceback.format_exc()))
        self.__notifier.notify(notifications.DatabaseLoaded(report))

    def __load_videos_from_disk(self, report: DatabaseReport):
        with Profiler(exit_message='Videos collected from disk:'):
            for video_folder_path in sorted(self.__video_folder_paths):
                self.__collect_videos_from_folder(video_folder_path, report)
        self.__notifier.notify(notifications.VideosCollectedFromDisk(report))
        self.__notifier.notify(notifications.StartedVideosLoading())
        count = report.count_from_disk()
        global_errors = []
        if count.collected:
            # Filter videos already loaded.
            video_paths_to_load = []
            for disk_report in report.disk.values():  # type: DiskReport
                for video_path in disk_report.collected:
                    if self.contains_absolute_path(video_path) and (
                            video_path.get_date_modified() == self.get(video_path).date_modified):
                        disk_report.already_loaded.append(video_path)
                    else:
                        video_paths_to_load.append(video_path)
            count_to_load = len(video_paths_to_load)
            if count.collected > count_to_load:
                self.__notifier.notify(notifications.VideosAlreadyLoadedFromDisk(report))
            if count_to_load:
                cpu_count = os.cpu_count()
                jobs = common.dispatch_tasks(video_paths_to_load, cpu_count, self.__max_id + 1)
                self.__max_id = self.__max_id + 1 + count_to_load
                job_function = functools.partial(load_videos_from_disk, self.__folder_path, self.notifier)
                with Profiler(exit_message='Finished to load %d videos:' % count.collected):
                    with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                        results = list(executor.map(job_function, jobs))
                for job_object in results:
                    for new_video in job_object.success:  # type: Video
                        disk_report = report.disk[new_video.absolute_path.get_dirname()]
                        if self.contains_absolute_path(new_video.absolute_path):
                            new_video.set_properties(self.get(new_video.absolute_path).properties)
                            disk_report.updated.append(new_video.absolute_path)
                        else:
                            new_video.set_properties(PropertyDict(self.__property_types))
                            disk_report.loaded.append(new_video.absolute_path)
                        self.add(new_video)
                    for video_path, traceback_string in job_object.errors:
                        disk_report = report.disk[video_path.get_dirname()]
                        disk_report.errors.append((video_path, traceback_string))
                    global_errors += job_object.global_errors
        self.__notifier.notify(notifications.FinishedVideosLoading(report, global_errors))

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
        self.__notifier.notify(notifications.VideosCollectedFromFolder(disk_report))

    def __delete_entry(self, video: Video, remove_video_definitively=False):
        entry_path = AbsolutePath.new_file_path(self.__folder_path, video.video_id, VIDEO_ENTRY_EXTENSION)
        assert entry_path.exists() and entry_path.isfile()
        entry_path.delete()
        video.delete_thumbnail()
        if self.contains_absolute_path(video.absolute_path):
            self.remove_from_absolute_path(video.absolute_path)
        if remove_video_definitively:
            video.absolute_path.delete()

    def ensure_thumbnails(self):
        videos_missing_thumbnail = []
        for video in self.videos():
            if not video.thumbnail:
                video.thumbnail = AbsolutePath.new_file_path(self.__folder_path, video.video_id, THUMBNAIL_EXTENSION)
            if not video.has_valid_thumbnail():
                videos_missing_thumbnail.append((video.absolute_path, video.video_id))

        errors = []
        self.notifier.notify(notifications.StartedThumbnailsGenerator())
        if videos_missing_thumbnail:
            cpu_count = os.cpu_count()
            jobs = common.dispatch_tasks(videos_missing_thumbnail, cpu_count, 1)
            job_function = functools.partial(generate_thumbnails, self.__folder_path, self.notifier)
            with Profiler(exit_message='Finished checking thumbnails:'):
                with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                    results = list(executor.map(job_function, jobs))
            for result in results:
                errors += result
        n_generated = sum(1 for path, _ in videos_missing_thumbnail if self.get(path).has_valid_thumbnail())
        self.notifier.notify(
            notifications.FinishedThumbnailsGenerator(n_generated, len(videos_missing_thumbnail), errors))

    def clean_database(self):
        if self.__keep_invalid_entries:
            return
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
            self.ensure_thumbnails()
        finally:
            self.save()
        return database_report

    def save_database_file(self):
        self.__ensure_database_folder()
        json_info = {
            'name': self.name,
            'video_folders': [str(path) for path in self.__video_folder_paths],
            'property_types': self.__property_types.to_json_data(),
            'not_found': self.__not_found
        }
        with open(self.__file_path.path, 'w') as file:
            json.dump(json_info, file, indent=2)

    def save_video(self, video: Video):
        """ Save one video object to database folder.
        :param video: video to save.
        :return: 1 if effectively saved, else 0.
        """
        if video.updated:
            db_video_path = AbsolutePath.new_file_path(self.__folder_path, video.video_id, VIDEO_ENTRY_EXTENSION)
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
