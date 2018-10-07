import concurrent.futures
import os
import traceback
import ujson as json
import whirlpool

from pysaurus.core import notifications, notifier, utils, videoraptor
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.c_message_parser import CMessageParser
from pysaurus.core.profile import Profiler
from pysaurus.core.video import Video

N_READS = videoraptor.get_n_reads()


class Database(object):
    __slots__ = ['list_path', 'json_path', 'database_path', '__folders', 'videos']

    @staticmethod
    def collect_files(folder_path: AbsolutePath, folder_to_files: dict):
        notifier.notify(notifications.CollectingFiles(folder_path))
        for file_name in folder_path.listdir():
            path = AbsolutePath.join(folder_path, file_name)
            if path.isdir():
                Database.collect_files(path, folder_to_files)
            elif utils.is_valid_video_filename(path.path):
                folder_to_files.setdefault(folder_path, set()).add(path)

    @staticmethod
    def get_folders_from_list_file(list_file_path: AbsolutePath):
        folders = set()
        if list_file_path.isfile():
            with open(list_file_path.path, 'r') as list_file:
                for line in list_file:
                    line = line.strip()
                    if line and line[0] != '#':
                        folders.add(AbsolutePath(line))
        return folders

    @staticmethod
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

    @staticmethod
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

    def get_videos_paths_from_disk(self):
        folder_to_files = {}
        for path in sorted(self.__folders):
            if not path.exists():
                notifier.notify(notifications.FolderNotFound(path))
            elif path.isdir():
                if path not in folder_to_files:
                    Database.collect_files(path, folder_to_files)
            elif utils.is_valid_video_filename(path.path):
                folder_to_files.setdefault(path.get_directory(), set()).add(path)
            else:
                notifier.notify(notifications.FolderIgnored(path))
        # Report collection.
        notifier.notify(notifications.CollectedFiles(folder_to_files))
        return folder_to_files

    def __init__(self, list_file_path):
        self.list_path = AbsolutePath.ensure(list_file_path)
        self.database_path = self.list_path.get_directory()
        self.json_path = AbsolutePath.new_file_path(self.database_path, self.list_path.title, 'json')
        self.__folders = Database.get_folders_from_list_file(self.list_path)
        self.videos = {}
        if self.json_path.isfile():
            with open(self.json_path.path, 'rb') as output_file:
                dictionaries = json.load(output_file)
            self.videos = {video.filename: video for video in (Video(dct, self.database_path) for dct in dictionaries)
                           if video.filename.get_directory() in self.__folders}

    def add_folder(self, folder):
        self.__folders.add(AbsolutePath.ensure(folder))

    def remove_folder(self, folder):
        folder = AbsolutePath.ensure(folder)
        if folder in self.__folders:
            self.__folders.remove(folder)

    def has_folder(self, folder):
        folder = AbsolutePath.ensure(folder)
        return folder in self.__folders

    def notify_database_loaded(self):
        nb_not_found = sum(not video.file_exists() for video in self.videos.values())
        notifier.notify(notifications.DatabaseLoaded(total=len(self.videos), not_found=nb_not_found))

    def update(self):
        folder_to_files = self.get_videos_paths_from_disk()
        cpu_count = os.cpu_count()
        errors = []
        messages = []
        video_errors = {}
        videos = {}
        tmp_videos = {}
        all_file_names = [file_name.path
                          for file_names in folder_to_files.values()
                          for file_name in file_names
                          if file_name not in self.videos]
        notifier.notify(notifications.VideosToLoad(len(all_file_names)))

        jobs = utils.dispatch_tasks(all_file_names, cpu_count)
        with Profiler(enter_message='Getting videos info through %d threads.' % len(jobs), exit_message='Got info:'):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                results = list(executor.map(Database.job_videos_info, jobs))

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
            prefix = CMessageParser.get_prefix(message)
            if prefix == CMessageParser.ERROR:
                errors.append(message[(len(prefix) + 1):])
            elif prefix == CMessageParser.VIDEO_ERROR:
                split_pos = message.index(']')
                file_name = AbsolutePath(utils.hex_to_string(message[(len(prefix) + 1):split_pos]))
                detail = message[(split_pos + 1):]
                if file_name in videos:
                    video_errors.setdefault(file_name, []).append(
                        'Unexpected known video with error (%s): %s ' % (file_name, detail))
                    videos.pop(file_name)
                elif file_name.path in remaining_file_names:
                    video_errors.setdefault(file_name, []).append(detail)
                else:
                    errors.append('Error for unknown video (%s): %s' % (file_name, detail))
            elif prefix == CMessageParser.VIDEO_WARNING:
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
        self.videos.update(videos)
        if errors:
            notifier.notify(notifications.InfoErrors(errors))
        if video_errors:
            notifier.notify(notifications.VideoInfoErrors(video_errors))
        if len(videos):
            self.save()

    def ensure_thumbnails(self):
        cpu_count = os.cpu_count()
        thumb_to_videos = {}
        file_names_no_thumbs = []
        for video in self.videos.values():
            if video.file_exists():
                if video.thumbnail_is_valid():
                    thumb_to_videos.setdefault(video.thumbnail, []).append(video)
                else:
                    file_names_no_thumbs.append(video.filename.path)
        for vds in thumb_to_videos.values():
            if len(vds) != 1:
                for v in vds:  # type: Video
                    v.thumbnail = None
                    file_names_no_thumbs.append(v.filename.path)

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
                thumb_path = AbsolutePath.new_file_path(self.database_path, thumb_name, utils.THUMBNAIL_EXTENSION)
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
            thumb_jobs.append((job_file_names, job_thumb_names, self.database_path.path, job_id))
        with Profiler(enter_message='Getting thumbnails through %d thread(s).' % len(thumb_jobs),
                      exit_message='Got thumbnails:'):
            with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
                thumb_results = list(executor.map(Database.job_videos_thumbnails, thumb_jobs))
        for local_thumb_messages, local_thumb_exceptions in thumb_results:
            thumb_errors.extend(local_thumb_exceptions)
            for inline_messages in local_thumb_messages:
                for message in inline_messages.splitlines():
                    message = message.strip()
                    if not message:
                        continue
                    prefix = CMessageParser.get_prefix(message)
                    if prefix == CMessageParser.ERROR:
                        thumb_errors.append(message[(len(prefix) + 1):])
                    elif prefix in (CMessageParser.VIDEO_ERROR, CMessageParser.VIDEO_WARNING):
                        split_pos = message.index(']')
                        file_name = AbsolutePath(utils.hex_to_string(message[(len(prefix) + 1):split_pos]))
                        detail = message[(split_pos + 1):]
                        if file_name.path in file_name_to_thumb_name:
                            thumb_video_errors.setdefault(file_name.path, []).append(
                                detail if prefix == CMessageParser.VIDEO_ERROR else '(warning) %s' % detail)
                        else:
                            thumb_errors.append('Thumbnail %s for unknown video (%s): %s'
                                                % (prefix[len('VIDEO_'):].lower(), file_name, detail))

        thumb_video_errors = {file_name: errors
                              for file_name, errors in thumb_video_errors.items()
                              if any(not message.startswith('(warning)') for message in errors)}

        for thumb_name, file_name in thumb_name_to_file_name.items():
            video = self.videos.get(AbsolutePath(file_name))  # type: Video
            video.thumbnail = AbsolutePath.new_file_path(self.database_path, thumb_name, utils.THUMBNAIL_EXTENSION)
        remaining_thumb_videos = [video.filename.path for video in self.videos.values()
                                  if video.file_exists() and not video.thumbnail_is_valid()]
        notifier.notify(notifications.MissingThumbnails(remaining_thumb_videos))
        if thumb_errors:
            notifier.notify(notifications.ThumbnailErrors(thumb_errors))
        if thumb_video_errors:
            notifier.notify(notifications.VideoThumbnailErrors(thumb_video_errors))
        if len(file_names_no_thumbs):
            self.save()

    def save(self):
        # Ensure database folder.
        self.database_path.mkdir()
        # Save list file.
        with open(self.list_path.path, 'w') as list_file:
            for folder in sorted(self.__folders):
                list_file.writelines(folder.path)
                list_file.writelines('\r\n')
        # Save videos entries.
        with open(self.json_path.path, 'w') as output_file:
            json.dump((video.to_dict() for video in self.videos.values()), output_file)
            notifier.notify(notifications.DatabaseSaved(len(self.videos)))
