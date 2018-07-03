import concurrent.futures
import os
import sys
import traceback
import ujson as json

from pyraptor import utils, videoraptor
from pyraptor.absolute_path import AbsolutePath
from pyraptor.profile import Profiler
from pyraptor.video import Video

N_READS = videoraptor.get_n_reads()


class MessageParser(object):
    ERROR = '#ERROR'
    FINISHED = '#FINISHED'
    IGNORED = '#IGNORED'
    LOADED = '#LOADED'
    MESSAGE = '#MESSAGE'
    USAGE = '#USAGE'
    VIDEO_ERROR = '#VIDEO_ERROR'
    VIDEO_WARNING = '#VIDEO_WARNING'
    WARNING = '#WARNING'

    __prefixes__ = (ERROR, FINISHED, IGNORED, LOADED, MESSAGE, USAGE, VIDEO_ERROR, VIDEO_WARNING, WARNING)

    @classmethod
    def get_prefix(cls, line):
        for prefix in cls.__prefixes__:
            if line.startswith(prefix):
                return prefix
        return None


def collect_files(folder_path: AbsolutePath, collector: dict):
    print('#COLLECTING', folder_path)
    for file_name in folder_path.listdir():
        path = AbsolutePath.join(folder_path, file_name)
        if path.isdir():
            collect_files(path, collector)
        elif utils.is_valid_video_filename(path.path):
            collector.setdefault(folder_path, []).append(path)


def collect_file(file_path: AbsolutePath, collector: dict):
    if utils.is_valid_video_filename(file_path.path):
        collector.setdefault(file_path.get_directory(), []).append(file_path)
        return True
    return False


def extract_info(job):
    tasks, job_id = job
    videos = []
    messages = []
    exceptions = []
    cursor = 0
    count_tasks = len(tasks)
    while cursor < count_tasks:
        print('[JOB %s] Extracted %d/%d video(s).' % (job_id, cursor, count_tasks))
        try:
            res, local_messages, local_videos = videoraptor.get_video_details(tasks[cursor:(cursor + N_READS)])
            if not res:
                exceptions.append(Exception(
                    '[JOB %s] Internal error after extracted %d/%d video(s).' % (job_id, cursor, count_tasks)))
            else:
                videos.append(local_videos)
            messages.append(local_messages)
            messages.append(videoraptor.pop_logger())
        except Exception as exc:
            exceptions.append(exc)
        cursor += N_READS
    print('[JOB %s] Finished extracting %d video(s).' % (job_id, count_tasks))
    return videos, messages, exceptions


def main():
    list_file_path = AbsolutePath(os.path.join('..', '.local', 'test_folder.log'))
    output_file_path = AbsolutePath.new_file_path(list_file_path.get_directory(), list_file_path.title, 'json')

    database = {}
    if output_file_path.exists() and output_file_path.isfile():
        with open(output_file_path.path, 'rb') as output_file:
            dictionaries = json.load(output_file)
        database = {video.filename : video for video in [Video(dct) for dct in dictionaries]}
        print('LOADED', len(database), 'video(s).')
        removed_videos = []
        for video in database.values():
            if not video.filename.exists():
                removed_videos.append(video)
        if removed_videos:
            for video in removed_videos:
                database.pop(video.filename)
            print('REMOVED', len(removed_videos), 'video(s).')

    folder_to_files = {}
    if not list_file_path.exists() or not list_file_path.isfile():
        raise Exception('Invalid file path: %s' % list_file_path)
    with open(list_file_path.path, 'r') as list_file:
        for line in list_file:
            line = line.strip()
            if line and line[0] != '#':
                path = AbsolutePath(line)
                if not path.exists():
                    print('#NOT_FOUND', path)
                elif path.isdir():
                    collect_files(path, folder_to_files)
                elif not collect_file(path, folder_to_files):
                    print('#IGNORED', path)

    # Report collection.
    print('%d\tTOTAL' % sum(len(file_names) for file_names in folder_to_files.values()))
    for path in sorted(folder_to_files.keys()):
        print('%d\t%s' % (len(folder_to_files[path]), path))

    videos = []
    messages = []
    errors = []
    video_errors = {}
    ignored = set()
    all_short_file_names = []
    short_to_long = {}
    for folder_file_names in folder_to_files.values():
        for file_name in folder_file_names:
            if file_name not in database:
                short_name = utils.get_convenient_os_path(file_name.path)
                short_to_long[short_name] = file_name
                all_short_file_names.append(short_name)
    print(len(all_short_file_names), 'video(s) to load.')
    cpu_count = os.cpu_count()
    jobs = utils.dispatch_tasks(all_short_file_names, cpu_count)

    with Profiler(exit_message='Files parsed:'):
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
            results = list(executor.map(extract_info, jobs))
    for (local_videos, local_messages, local_exceptions) in results:
        for batch_videos in local_videos:
            videos.extend(batch_videos)
        for exception in local_exceptions:  # type: Exception
            printer = utils.StringPrinter()
            printer.write('Error while loading videos from disk.')
            traceback.print_tb(exception.__traceback__, file=printer.string_buffer)
            printer.write(type(exception).__name__)
            printer.write(exception)
            errors.append(str(printer))
        for message in local_messages:
            for inline_message in message.splitlines():
                inline_message = inline_message.strip()
                if inline_message:
                    messages.append(inline_message)
    print('PARSED:')
    print('%d\tvideo(s)' % len(videos))
    print('%d\tmessage(s)' % len(messages))

    # Updating videos.
    tmp_database = {video.filename: video for video in videos if video.filename}
    # Parsing messages.
    for message in messages:
        prefix = MessageParser.get_prefix(message)
        if prefix == MessageParser.ERROR:
            errors.append(message[(len(prefix) + 1):])
        elif prefix == MessageParser.IGNORED:
            file_name = AbsolutePath(message[(len(prefix) + 1):])
            ignored.add(file_name)
            short_to_long.pop(file_name.path)
        elif prefix == MessageParser.VIDEO_ERROR:
            split_pos = message.index(']')
            file_name = AbsolutePath(message[(len(prefix) + 1):split_pos])
            detail = message[(split_pos + 1):]
            if file_name in tmp_database:
                errors.append('Error for a video (%s): %s' % (file_name, detail))
                tmp_database.pop(file_name)
                short_to_long.pop(file_name.path)
            else:
                video_errors.setdefault(file_name, []).append(detail)
        elif prefix == MessageParser.VIDEO_WARNING:
            split_pos = message.index(']')
            file_name = AbsolutePath(message[(len(prefix) + 1):split_pos])
            detail = message[(split_pos + 1):]
            if file_name in tmp_database:
                tmp_database[file_name].warnings.add(detail)
                errors.append('Warning for unknown video (%s): %s' % (file_name, detail))
            elif file_name not in ignored:
                errors.append('Warning for unknown video (%s): %s' % (file_name, detail))
    for video in tmp_database.values():  # type: Video
        try:
            video.filename = short_to_long.pop(video.filename.path)
        except Exception as exc:
            traceback.print_tb(exc.__traceback__, file=sys.stdout)
            print(exc)
            print(video)
    if short_to_long:
        errors.append("Internal errors: some video files are never retrieved after parsing.\n%s" % '\n'.join(
            '[short name] %s => [long name] %s' % (short_name, long_name)
            for short_name, long_name in short_to_long.items()
        ))
    database.update(tmp_database)
    if all_short_file_names:
        with open(output_file_path.path, 'w') as output_file:
            json.dump((video.to_dict() for video in database.values()), output_file, indent=2)
            print('SAVED')
    if ignored:
        print('%d\tIGNORED' % len(ignored))
        for ignored_file_name in ignored:
            print('\t%s' % ignored_file_name)
    if errors:
        print('%d\tERROR(S)' % len(errors))
        for error in errors:
            print('=' * 80)
            print(error)
    if video_errors:
        print('%d\tVIDEO ERROR(S)' % len(video_errors))
        for file_name in sorted(video_errors.keys()):
            len_file_name = len(file_name.path)
            print('=' * len_file_name)
            print(file_name)
            print('=' * len_file_name)
            print('\n'.join(video_errors[file_name]))


if __name__ == '__main__':
    main()
