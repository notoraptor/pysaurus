import concurrent.futures
import codecs
import os
import whirlpool
import traceback
import ujson as json

from pyraptor import utils, videoraptor
from pyraptor.absolute_path import AbsolutePath
from pyraptor.profile import Profiler
from pyraptor.video import Video

N_READS = videoraptor.get_n_reads()


class MessageParser(object):
    ERROR = '#ERROR'
    MESSAGE = '#MESSAGE'
    VIDEO_ERROR = '#VIDEO_ERROR'
    VIDEO_WARNING = '#VIDEO_WARNING'
    WARNING = '#WARNING'

    __prefixes__ = (ERROR, MESSAGE, VIDEO_ERROR, VIDEO_WARNING, WARNING)

    @classmethod
    def get_prefix(cls, line):
        for prefix in cls.__prefixes__:
            if line.startswith(prefix):
                return prefix
        return None


def decode_hexadecimal(message):
    return codecs.decode(message, 'hex').decode()


def collect_files(folder_path: AbsolutePath, collector: dict):
    print('#COLLECTING', folder_path)
    for file_name in folder_path.listdir():
        path = AbsolutePath.join(folder_path, file_name)
        if path.isdir():
            collect_files(path, collector)
        elif utils.is_valid_video_filename(path.path):
            collector.setdefault(folder_path, set()).add(path)


def extract_info(job):
    file_names, job_id = job
    videos = []
    messages = []
    exceptions = []
    cursor = 0
    count_tasks = len(file_names)
    while cursor < count_tasks:
        print('[JOB %s] Extracted %d/%d video(s).' % (job_id, cursor, count_tasks))
        try:
            res, local_messages, local_videos = videoraptor.get_video_details(file_names[cursor:(cursor + N_READS)])
            if res:
                videos.append(local_videos)
            else:
                messages.append('#ERROR [JOB %s] Internal error (%d) after extracted %d/%d video(s).' % (job_id, res, cursor, count_tasks))
            messages.append(local_messages)
        except Exception as exc:
            printer = utils.StringPrinter()
            printer.write('Error while loading videos from disk.')
            traceback.print_tb(exc.__traceback__, file=printer.string_buffer)
            printer.write(type(exc).__name__)
            printer.write(exc)
            exceptions.append(str(printer))
        cursor += N_READS
    print('[JOB %s] Finished extracting %d video(s).' % (job_id, count_tasks))
    return videos, messages, exceptions


def generate_thumbnails(job):
    file_names, thumb_names, thumb_folder, job_id = job
    messages = []
    exceptions = []
    cursor = 0
    count_tasks = len(file_names)
    while cursor < count_tasks:
        print('[JOB %s] Generated %d/%d thumbnail(s).' % (job_id, cursor, count_tasks))
        try:
            res, local_messages = videoraptor.generate_thumbnails(
                file_names[cursor:(cursor + N_READS)],
                thumb_names[cursor:(cursor + N_READS)],
                thumb_folder
            )
            if not res:
                messages.append('#ERROR [JOB %s] Internal error after generated %d/%d thumbnail(s).' % (job_id, cursor, count_tasks))
            messages.append(local_messages)
        except Exception as exc:
            printer = utils.StringPrinter()
            printer.write('Error while generating thumbnails.')
            traceback.print_tb(exc.__traceback__, file=printer.string_buffer)
            printer.write(type(exc).__name__)
            printer.write(exc)
            exceptions.append(str(printer))
        cursor += N_READS
    print('[JOB %s] Finished generating %d thumbnail(s).' % (job_id, count_tasks))
    return messages, exceptions


def ensure_thumbnails(database: dict, output_folder: AbsolutePath, cpu_count: int):
    vfnames_without_thumbs = [video.filename.path for video in database.values() if not video.thumbnail_is_valid()]
    if vfnames_without_thumbs:
        thumb_video_errors = {}
        thumb_errors = []
        thumb_jobs = []
        thumb_name_to_file_name = {}
        file_name_to_thumb_name = {}
        wp = whirlpool.new()
        for file_name in vfnames_without_thumbs:
            wp.update(file_name.encode())
            base_thumb_name = wp.hexdigest().lower()
            thumb_name_index = 0
            thumb_name = base_thumb_name
            while True:
                thumb_path = AbsolutePath.new_file_path(output_folder, thumb_name, utils.THUMBNAIL_EXTENSION)
                if thumb_name in thumb_name_to_file_name or (thumb_path.exists() and thumb_path.isfile()):
                    thumb_name_index += 1
                    thumb_name = '%s_%d' % (base_thumb_name, thumb_name_index)
                else:
                    break
            thumb_name_to_file_name[thumb_name] = file_name
            file_name_to_thumb_name[file_name] = thumb_name
        dispatched_thumb_jobs = utils.dispatch_tasks(vfnames_without_thumbs, cpu_count)
        for job_file_names, job_id in dispatched_thumb_jobs:
            job_thumb_names = [file_name_to_thumb_name[file_name] for file_name in job_file_names]
            thumb_jobs.append((job_file_names, job_thumb_names, output_folder.path, job_id))
        with Profiler(enter_message='Generating thumbnails through %d jobs.' % len(thumb_jobs),
                      exit_message='Thumbnails generated:'):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                thumb_results = list(executor.map(generate_thumbnails, thumb_jobs))
        for local_thumb_messages, local_thumb_exceptions in thumb_results:
            thumb_errors.extend(local_thumb_exceptions)
            for inline_messages in local_thumb_messages:
                for message in inline_messages.splitlines():
                    message = message.strip()
                    if not message:
                        continue
                    prefix = MessageParser.get_prefix(message)
                    if prefix == MessageParser.ERROR:
                        thumb_errors.append(message[(len(prefix) + 1):])
                    elif prefix in (MessageParser.VIDEO_ERROR, MessageParser.VIDEO_WARNING):
                        split_pos = message.index(']')
                        file_name = AbsolutePath(decode_hexadecimal(message[(len(prefix) + 1):split_pos]))
                        detail = message[(split_pos + 1):]
                        if file_name.path in file_name_to_thumb_name:
                            thumb_video_errors.setdefault(file_name.path, []).append(
                                detail if prefix == MessageParser.VIDEO_ERROR else '(warning) %s' % detail)
                        else:
                            thumb_errors.append('Thumbnail %s for unknown video (%s): %s'
                                                % (prefix[len('VIDEO_'):].lower(), file_name, detail))

        for thumb_name, file_name in thumb_name_to_file_name.items():
            video = database.get(AbsolutePath(file_name))  # type: Video
            video.thumbnail = AbsolutePath.new_file_path(output_folder, thumb_name, utils.THUMBNAIL_EXTENSION)
        remaining_thumb_videos = [video.filename.path for video in database.values() if not video.thumbnail_is_valid()]
        if remaining_thumb_videos:
            printer = utils.StringPrinter()
            printer.write(
                'Internal errors: %d video(s) still without thumbnails.' % len(remaining_thumb_videos))
            for remaining_file_name in remaining_thumb_videos:
                printer.write('\t%s' % remaining_file_name)
            thumb_errors.append(str(printer))
        if thumb_errors:
            print('%d\tTHUMBNAIL ERROR(S)' % len(thumb_errors))
            for error in thumb_errors:
                print('(error)', error)
        if thumb_video_errors:
            print('%d\tTHUMBNAIL VIDEO ERROR(S)' % len(thumb_video_errors))
            for file_name in sorted(thumb_video_errors.keys()):
                utils.print_title(file_name)
                for error in thumb_video_errors[file_name]:
                    print('\t%s' % error)
    return len(vfnames_without_thumbs)


def get_same_sizes(database: dict):
    sizes = {}
    for video in database.values():
        if video.file_exists:
            sizes.setdefault(video.size, []).append(video)
    duplicated_sizes = {size: elements for (size, elements) in sizes.items() if len(elements) > 1}
    if duplicated_sizes:
        print()
        utils.print_title('%d DUPLICATE CASE(S)' % len(duplicated_sizes))
        for size in sorted(duplicated_sizes.keys()):
            elements = duplicated_sizes[size]  # type: list
            elements.sort(key=lambda v: v.filename)
            print(size, 'bytes,', len(elements), 'video(s)')
            for video in elements:
                print('\t"%s"' % video.filename)


def save_database(database: dict, output_file_path: AbsolutePath):
    with open(output_file_path.path, 'w') as output_file:
        json.dump((video.to_dict() for video in database.values()), output_file, indent=1)
        print(len(database), 'SAVED')


def find(database: dict, term: str):
    term = term.lower()
    found = []
    for video in database.values():
        if term in video.filename.title.lower() or (video.title and term in video.title.lower()):
            found.append(video)
    print(len(found), 'FOUND', term)
    found.sort(key=lambda v: v.filename)
    for video in found:
        print('\t"%s"' % video.filename)


def main():
    list_file_path = AbsolutePath(os.path.join('..', '.local', 'test_folder.log'))
    output_folder = list_file_path.get_directory()
    output_file_path = AbsolutePath.new_file_path(output_folder, list_file_path.title, 'json')

    # Loading database.
    database = {}
    if output_file_path.isfile():
        with open(output_file_path.path, 'rb') as output_file:
            dictionaries = json.load(output_file)
        database = {video.filename: video for video in [Video(dct) for dct in dictionaries]}
        print('LOADED', len(database), 'video(s).')
        nb_not_found = 0
        for video in database.values():
            if not video.file_exists:
                nb_not_found += 1
        if nb_not_found:
            print('NOT FOUND', nb_not_found, 'video(s).')

    # Update database.
    folder_to_files = {}
    if not list_file_path.exists() or not list_file_path.isfile():
        raise Exception('Invalid file path: %s' % list_file_path)
    with open(list_file_path.path, 'r') as list_file:
        for line in list_file:
            line = line.strip()
            if line and line[0] != '#':
                path = AbsolutePath(line)
                if not path.exists():
                    print('NOT FOUND', path)
                elif path.isdir():
                    if path not in folder_to_files:
                        collect_files(path, folder_to_files)
                elif utils.is_valid_video_filename(path.path):
                    folder_to_files.setdefault(path.get_directory(), set()).add(path)
                else:
                    print('IGNORED', path)

    # Report collection.
    print('%d\tTOTAL' % sum(len(file_names) for file_names in folder_to_files.values()))
    for path in sorted(folder_to_files.keys()):
        print('%d\t%s' % (len(folder_to_files[path]), path))

    errors = []
    messages = []
    video_errors = {}
    videos = {}
    all_file_names = [file_name.path
                      for file_names in folder_to_files.values()
                      for file_name in file_names
                      if file_name not in database]
    print(len(all_file_names), 'video(s) to load.')

    cpu_count = os.cpu_count()
    jobs = utils.dispatch_tasks(all_file_names, cpu_count)
    with Profiler(enter_message='Running %d jobs.' % len(jobs), exit_message='Files parsed:'):
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
            results = list(executor.map(extract_info, jobs))

    for (local_videos, local_messages, local_exceptions) in results:
        for batch_videos in local_videos:
            for video in batch_videos:
                if video.filename:
                    if video.filename.path not in all_file_names:
                        errors.append('Unknown parsed video short name %s' % video.filename.path)
                    else:
                        videos[video.filename] = video
        errors.extend(local_exceptions)
        for message in local_messages:
            for inline_message in message.splitlines():
                inline_message = inline_message.strip()
                if inline_message:
                    messages.append(inline_message)
    print('PARSED:')
    print('%d\tvideo(s)' % len(videos))
    print('%d\tmessage(s)' % len(messages))
    # for msg in messages: print('\t%s' % msg)

    # Updating videos.
    # Parsing messages.
    for message in messages:
        prefix = MessageParser.get_prefix(message)
        if prefix == MessageParser.ERROR:
            errors.append(message[(len(prefix) + 1):])
        elif prefix == MessageParser.VIDEO_ERROR:
            split_pos = message.index(']')
            file_name = AbsolutePath(decode_hexadecimal(message[(len(prefix) + 1):split_pos]))
            detail = message[(split_pos + 1):]
            if file_name in videos:
                errors.append('Unexpected known video with error (%s): %s ' % (file_name, detail))
                videos.pop(file_name)
            if file_name.path in all_file_names:
                video_errors.setdefault(file_name, []).append(detail)
            else:
                errors.append('Error for unknown video (%s): %s' % (file_name, detail))
        elif prefix == MessageParser.VIDEO_WARNING:
            split_pos = message.index(']')
            file_name = AbsolutePath(decode_hexadecimal(message[(len(prefix) + 1):split_pos]))
            detail = message[(split_pos + 1):]
            if file_name in videos:
                videos[file_name].warnings.add(detail)
            elif file_name.path in all_file_names:
                video_errors.setdefault(file_name, []).append('(warning) %s' % detail)
            else:
                errors.append('Warning for unknown video (%s): %s' % (file_name, detail))
    remaining_file_names = []
    for file_name in all_file_names:
        file_path = AbsolutePath(file_name)
        if file_path not in video_errors and file_path not in videos:
            remaining_file_names.append(file_path)
    if remaining_file_names:
        printer = utils.StringPrinter()
        printer.write('Internal errors: %d video files are never retrieved after parsing.' % len(remaining_file_names))
        for remaining_file_name in remaining_file_names:
            printer.write('\t%s' % remaining_file_name)
        errors.append(str(printer))
    database.update({video.filename: video for video in videos.values()})

    if videos:
        save_database(database, output_file_path)

    if errors:
        print('%d\tERROR(S)' % len(errors))
        for error in errors:
            print('(error)', error)
    if video_errors:
        print('%d\tVIDEO ERROR(S)' % len(video_errors))
        for file_name in sorted(video_errors.keys()):
            utils.print_title(file_name)
            for error in video_errors[file_name]:
                print('\t%s' % error)

    # Generating thumbnails.
    had_work = ensure_thumbnails(database, output_folder, cpu_count)

    if had_work:
        save_database(database, output_file_path)

    get_same_sizes(database)


if __name__ == '__main__':
    main()
