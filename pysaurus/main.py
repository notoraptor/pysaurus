import concurrent.futures
import os
import whirlpool
import traceback
import ujson as json

from pysaurus import utils, videoraptor
from pysaurus.absolute_path import AbsolutePath
from pysaurus.profile import Profiler
from pysaurus.video import Video
from pysaurus import features, notifier, notifications

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


def collect_files(folder_path: AbsolutePath, folder_to_files: dict):
    notifier.notify(notifications.CollectingFiles(folder_path))
    for file_name in folder_path.listdir():
        path = AbsolutePath.join(folder_path, file_name)
        if path.isdir():
            collect_files(path, folder_to_files)
        elif utils.is_valid_video_filename(path.path):
            folder_to_files.setdefault(folder_path, set()).add(path)


def job_videos_info(job):
    file_names, job_id = job
    videos = []
    messages = []
    exceptions = []
    cursor = 0
    count_tasks = len(file_names)
    while cursor < count_tasks:
        notifier.notify(notifications.VideoJob(job_id, cursor, count_tasks))
        try:
            res, local_messages, local_videos = videoraptor.get_video_details(file_names[cursor:(cursor + N_READS)])
            if res:
                videos.append(local_videos)
            else:
                messages.append('#ERROR [JOB %s] Internal error (%d) after extracted %d/%d video(s).' % (
                    job_id, res, cursor, count_tasks))
            messages.append(local_messages)
        except Exception as exc:
            printer = utils.StringPrinter()
            printer.write('Error while loading videos from disk.')
            traceback.print_tb(exc.__traceback__, file=printer.string_buffer)
            printer.write(type(exc).__name__)
            printer.write(exc)
            exceptions.append(str(printer))
        cursor += N_READS
    notifier.notify(notifications.VideoJob(job_id, count_tasks, count_tasks))
    return videos, messages, exceptions


def job_videos_thumbnails(job):
    file_names, thumb_names, thumb_folder, job_id = job
    messages = []
    exceptions = []
    cursor = 0
    count_tasks = len(file_names)
    while cursor < count_tasks:
        notifier.notify(notifications.ThumbnailJob(job_id, cursor, count_tasks))
        try:
            res, local_messages = videoraptor.generate_thumbnails(
                file_names[cursor:(cursor + N_READS)], thumb_names[cursor:(cursor + N_READS)], thumb_folder
            )
            if not res:
                messages.append('#ERROR [JOB %s] Internal error after generated %d/%d thumbnail(s).' % (
                    job_id, cursor, count_tasks))
            messages.append(local_messages)
        except Exception as exc:
            printer = utils.StringPrinter()
            printer.write('Error while generating thumbnails.')
            traceback.print_tb(exc.__traceback__, file=printer.string_buffer)
            printer.write(type(exc).__name__)
            printer.write(exc)
            exceptions.append(str(printer))
        cursor += N_READS
    notifier.notify(notifications.ThumbnailJob(job_id, count_tasks, count_tasks))
    return messages, exceptions


def load_database(output_file_path: AbsolutePath):
    database = {}
    if output_file_path.isfile():
        with open(output_file_path.path, 'rb') as output_file:
            dictionaries = json.load(output_file)
        database = {video.filename: video for video in (Video(dct) for dct in dictionaries)}
        nb_not_found = sum(not video.file_exists for video in database.values())
        notifier.notify(notifications.DatabaseLoaded(total=len(database), not_found=nb_not_found))
    return database


def parse_folders_list_file(list_file_path: AbsolutePath):
    folder_to_files = {}
    if not list_file_path.exists() or not list_file_path.isfile():
        raise Exception('Invalid file path: %s' % list_file_path)
    with open(list_file_path.path, 'r') as list_file:
        for line in list_file:
            line = line.strip()
            if line and line[0] != '#':
                path = AbsolutePath(line)
                if not path.exists():
                    notifier.notify(notifications.FolderNotFound(path))
                elif path.isdir():
                    if path not in folder_to_files:
                        collect_files(path, folder_to_files)
                elif utils.is_valid_video_filename(path.path):
                    folder_to_files.setdefault(path.get_directory(), set()).add(path)
                else:
                    notifier.notify(notifications.FolderIgnored(path))
    # Report collection.
    notifier.notify(notifications.CollectedFiles(folder_to_files))
    return folder_to_files


def update_database(database: dict, folder_to_files: dict, cpu_count: int):
    errors = []
    messages = []
    video_errors = {}
    videos = {}
    tmp_videos = {}
    all_file_names = [file_name.path
                      for file_names in folder_to_files.values()
                      for file_name in file_names
                      if file_name not in database]
    notifier.notify(notifications.VideosToLoad(len(all_file_names)))

    jobs = utils.dispatch_tasks(all_file_names, cpu_count)
    with Profiler(enter_message='Getting videos info through %d threads.' % len(jobs), exit_message='Got info:'):
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
            results = list(executor.map(job_videos_info, jobs))

    for (local_videos, local_messages, local_exceptions) in results:
        for batch_videos in local_videos:
            for video in batch_videos:
                if video.filename:
                    if video.filename.path in tmp_videos:
                        errors.append('Unexpected duplicated info for video %s' % video.filename)
                    else:
                        tmp_videos[video.filename.path] = video
        errors.extend(local_exceptions)
        for message in local_messages:
            for inline_message in message.splitlines():
                inline_message = inline_message.strip()
                if inline_message:
                    messages.append(inline_message)
    remaining_file_names = set()
    for file_name in all_file_names:
        if file_name in tmp_videos:
            video = tmp_videos.pop(file_name)
            videos[video.filename] = video
        else:
            remaining_file_names.add(file_name)
    for file_name in tmp_videos:
        errors.append('Unknown parsed video: %s' % file_name)
    notifier.notify(notifications.VideosLoaded(len(videos)))

    # Parsing messages.
    for message in messages:
        prefix = MessageParser.get_prefix(message)
        if prefix == MessageParser.ERROR:
            errors.append(message[(len(prefix) + 1):])
        elif prefix == MessageParser.VIDEO_ERROR:
            split_pos = message.index(']')
            file_name = AbsolutePath(utils.hex_to_string(message[(len(prefix) + 1):split_pos]))
            detail = message[(split_pos + 1):]
            if file_name in videos:
                video_errors.setdefault(file_name, []).append('Unexpected known video with error (%s): %s ' % (file_name, detail))
                videos.pop(file_name)
            elif file_name.path in remaining_file_names:
                video_errors.setdefault(file_name, []).append(detail)
            else:
                errors.append('Error for unknown video (%s): %s' % (file_name, detail))
        elif prefix == MessageParser.VIDEO_WARNING:
            split_pos = message.index(']')
            file_name = AbsolutePath(utils.hex_to_string(message[(len(prefix) + 1):split_pos]))
            detail = message[(split_pos + 1):]
            if file_name in videos:
                videos[file_name].warnings.add(detail)
            elif file_name.path in remaining_file_names:
                video_errors.setdefault(file_name, []).append('(warning) %s' % detail)
            else:
                errors.append('Warning for unknown video (%s): %s' % (file_name, detail))
    remaining_file_names.difference_update(file_name.path for file_name in video_errors)
    notifier.notify(notifications.MissingVideos(remaining_file_names))
    database.update(videos)
    if errors:
        notifier.notify(notifications.InfoErrors(errors))
    if video_errors:
        notifier.notify(notifications.VideoInfoErrors(video_errors))
    return len(videos)


def ensure_videos_thumbnails(database: dict, output_folder: AbsolutePath, cpu_count: int):
    file_names_no_thumbs = [video.filename.path for video in database.values() if not video.thumbnail_is_valid()]
    notifier.notify(notifications.ThumbnailsToLoad(len(file_names_no_thumbs)))
    if not file_names_no_thumbs:
        return 0
    thumb_video_errors = {}
    thumb_errors = []
    thumb_jobs = []
    thumb_name_to_file_name = {}
    file_name_to_thumb_name = {}
    wp = whirlpool.new()
    for file_name in file_names_no_thumbs:
        wp.update(file_name.encode())
        base_thumb_name = wp.hexdigest().lower()
        thumb_name_index = 0
        thumb_name = base_thumb_name
        while True:
            thumb_path = AbsolutePath.new_file_path(output_folder, thumb_name, utils.THUMBNAIL_EXTENSION)
            if thumb_name in thumb_name_to_file_name or thumb_path.exists():
                thumb_name_index += 1
                thumb_name = '%s_%d' % (base_thumb_name, thumb_name_index)
            else:
                break
        thumb_name_to_file_name[thumb_name] = file_name
        file_name_to_thumb_name[file_name] = thumb_name
    dispatched_thumb_jobs = utils.dispatch_tasks(file_names_no_thumbs, cpu_count)
    for job_file_names, job_id in dispatched_thumb_jobs:
        job_thumb_names = [file_name_to_thumb_name[file_name] for file_name in job_file_names]
        thumb_jobs.append((job_file_names, job_thumb_names, output_folder.path, job_id))
    with Profiler(enter_message='Getting thumbnails through %d thread(s).' % len(thumb_jobs),
                  exit_message='Got thumbnails:'):
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
            thumb_results = list(executor.map(job_videos_thumbnails, thumb_jobs))
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
                    file_name = AbsolutePath(utils.hex_to_string(message[(len(prefix) + 1):split_pos]))
                    detail = message[(split_pos + 1):]
                    if file_name.path in file_name_to_thumb_name:
                        thumb_video_errors.setdefault(file_name.path, []).append(
                            detail if prefix == MessageParser.VIDEO_ERROR else '(warning) %s' % detail)
                    else:
                        thumb_errors.append('Thumbnail %s for unknown video (%s): %s'
                                            % (prefix[len('VIDEO_'):].lower(), file_name, detail))

    thumb_video_errors = {file_name: errors
                          for file_name, errors in thumb_video_errors.items()
                          if any(not message.startswith('(warning)') for message in errors)}

    for thumb_name, file_name in thumb_name_to_file_name.items():
        video = database.get(AbsolutePath(file_name))  # type: Video
        video.thumbnail = AbsolutePath.new_file_path(output_folder, thumb_name, utils.THUMBNAIL_EXTENSION)
    remaining_thumb_videos = [video.filename.path for video in database.values() if not video.thumbnail_is_valid()]
    notifier.notify(notifications.MissingThumbnails(remaining_thumb_videos))
    if thumb_errors:
        notifier.notify(notifications.ThumbnailErrors(thumb_errors))
    if thumb_video_errors:
        notifier.notify(notifications.VideoThumbnailErrors(thumb_video_errors))
    return len(file_names_no_thumbs)


def save_database(database: dict, output_file_path: AbsolutePath):
    with open(output_file_path.path, 'w') as output_file:
        json.dump((video.to_dict() for video in database.values()), output_file, indent=1)
        notifier.notify(notifications.DatabaseSaved(len(database)))


def main():
    list_file_path = AbsolutePath(os.path.join('..', '.local', 'test_folder.log'))
    output_folder = list_file_path.get_directory()
    output_file_path = AbsolutePath.new_file_path(output_folder, list_file_path.title, 'json')
    cpu_count = os.cpu_count()

    # Loading database.
    database = load_database(output_file_path)

    # Update database.
    folder_to_files = parse_folders_list_file(list_file_path)
    n_loaded = update_database(database, folder_to_files, cpu_count)
    if n_loaded:
        save_database(database, output_file_path)

    # Generating thumbnails.
    n_created = ensure_videos_thumbnails(database, output_folder, cpu_count)
    if n_created:
        save_database(database, output_file_path)

    features.get_same_sizes(database)


if __name__ == '__main__':
    main()
