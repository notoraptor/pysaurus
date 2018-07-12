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
            collector.setdefault(folder_path, set()).add(path)


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


def get_same_sizes(database):
    sizes = {}
    for video in database.values():
        if video.file_exists:
            sizes.setdefault(video.size, []).append(video)
    duplicated_sizes = {size: elements for (size, elements) in sizes.items() if len(elements) > 1}
    for size in sorted(duplicated_sizes.keys()):
        elements = duplicated_sizes[size]  # type: list
        elements.sort(key=lambda v: v.filename)
        print(size, 'bytes,', len(elements), 'video(s)')
        for video in elements:
            print('\t"%s"' % video.filename)


def find(database: dict, term: str):
    term = term.lower()
    found = []
    for file_name in sorted(database.keys()):
        video = database[file_name]  # type: Video
        if term in video.filename.title.lower() or (video.title and term in video.title.lower()):
            found.append(video)
    print(len(found), 'FOUND', term)
    for video in found:
        print('\t"%s"' % video.filename)


def main():
    list_file_path = AbsolutePath(os.path.join('..', '.local', 'test_folder.log'))
    output_file_path = AbsolutePath.new_file_path(list_file_path.get_directory(), list_file_path.title, 'json')

    database = {}
    if output_file_path.isfile():
        with open(output_file_path.path, 'rb') as output_file:
            dictionaries = json.load(output_file)
        database = {video.filename: video for video in [Video(dct) for dct in dictionaries]}
        print('LOADED', len(database), 'video(s).')
        nb_not_found = 0
        for video in database.values():
            video.file_exists = video.filename.exists()
            if not video.file_exists:
                nb_not_found += 1
        if nb_not_found:
            print('NOT FOUND', nb_not_found, 'video(s).')

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
                    if path not in folder_to_files:
                        collect_files(path, folder_to_files)
                elif utils.is_valid_video_filename(path.path):
                    folder_to_files.setdefault(path.get_directory(), set()).add(path)
                else:
                    print('#IGNORED', path)

    # Report collection.
    print('%d\tTOTAL' % sum(len(file_names) for file_names in folder_to_files.values()))
    for path in sorted(folder_to_files.keys()):
        print('%d\t%s' % (len(folder_to_files[path]), path))

    errors = []
    messages = []
    video_errors = {}
    videos = {}
    short_to_long = {}
    for folder_file_names in folder_to_files.values():
        for file_name in folder_file_names:
            if file_name not in database:
                short_to_long[utils.get_convenient_os_path(file_name.path)] = file_name
    print(len(short_to_long), 'video(s) to load.')

    all_short_file_names = list(sorted(short_to_long.keys()))
    cpu_count = os.cpu_count()
    jobs = utils.dispatch_tasks(all_short_file_names, cpu_count)
    with Profiler(exit_message='Files parsed:'):
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
            results = list(executor.map(extract_info, jobs))

    for (local_videos, local_messages, local_exceptions) in results:
        for batch_videos in local_videos:
            for video in batch_videos:
                if video.filename:
                    if video.filename.path not in short_to_long:
                        errors.append('Unknown parsed video short name %s' % video.filename.path)
                    else:
                        videos[video.filename] = video
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
    # Parsing messages.
    for message in messages:
        prefix = MessageParser.get_prefix(message)
        if prefix == MessageParser.ERROR:
            errors.append(message[(len(prefix) + 1):])
        elif prefix == MessageParser.VIDEO_ERROR:
            split_pos = message.index(']')
            file_name = AbsolutePath(message[(len(prefix) + 1):split_pos])
            detail = message[(split_pos + 1):]
            if file_name in videos and videos[file_name].filename:
                # Video seems to have been extracted. Let's consider this error as a warning.
                videos[file_name].warnings.add(detail)
            elif file_name.path in short_to_long:
                video_errors.setdefault(file_name, []).append(detail)
                if file_name in videos:
                    videos.pop(file_name)
            else:
                errors.append('Error for unknown video (%s): %s' % (file_name, detail))
        elif prefix == MessageParser.VIDEO_WARNING:
            split_pos = message.index(']')
            file_name = AbsolutePath(message[(len(prefix) + 1):split_pos])
            detail = message[(split_pos + 1):]
            if file_name in videos:
                videos[file_name].warnings.add(detail)
            elif file_name.path not in short_to_long:
                errors.append('Warning for unknown video (%s): %s' % (file_name, detail))
            else:
                video_errors.setdefault(file_name, []).append('(warning) %s' % detail)
    video_errors = {short_to_long.pop(key.path, key): video_errors[key] for key in video_errors}
    for video in list(videos.values()):
        if video.filename.path in short_to_long:
            video.filename = short_to_long.pop(video.filename.path)
        else:
            videos.pop(video.filename)
            errors.append('Parsed video with unknown short name %s' % video.filename)
    if short_to_long:
        errors.append("Internal errors: some video files are never retrieved after parsing.\n%s" % '\n'.join(
            '[short name] %s => [long name] %s' % (short_name, long_name)
            for short_name, long_name in short_to_long.items()
        ))
    database.update({video.filename: video for video in videos.values()})
    if all_short_file_names:
        with open(output_file_path.path, 'w') as output_file:
            json.dump((video.to_dict() for video in database.values()), output_file, indent=2)
            print(len(database), 'SAVED')
    if errors:
        print('%d\tERROR(S)' % len(errors))
        for error in errors:
            print('(error)', error)
    if video_errors:
        print('%d\tVIDEO ERROR(S)' % len(video_errors))
        for file_name in sorted(video_errors.keys()):
            utils.print_title(file_name)
            for error in video_errors[file_name]:
                print(error)

    get_same_sizes(database)


if __name__ == '__main__':
    main()
