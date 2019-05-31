import os
import subprocess
import sys
from typing import Any

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.database import Database
from pysaurus.core.table import Table
from pysaurus.core.utils import functions as utils
from pysaurus.core.video import Video

NbType = utils.enumeration(('entries', 'unreadable', 'not_found', 'valid', 'found', 'thumbnails'))
FieldType = utils.enumeration((
    # Video class fields
    'filename', 'title', 'container_format', 'audio_codec', 'video_codec', 'width', 'height', 'sample_rate', 'bit_rate',
    # special fields
    'size', 'duration', 'frame_rate', 'name',
))


def get_video_info(video, field):
    # type: (Video, str) -> Any
    if field == 'size':
        return video.get_size()
    if field == 'duration':
        return video.get_duration()
    if field == 'frame_rate':
        return video.frame_rate_num / video.frame_rate_den
    if field == 'name':
        return video.get_title()
    return getattr(video, field)


class Interface:
    __slots__ = 'database',

    def __init__(self):
        self.database = Interface.load_database()

    @staticmethod
    def load_database():
        list_file_path = AbsolutePath(os.path.join(utils.package_dir(), '..', '..', '.local', 'test_folder.log'))
        return Database.load_from_list_file(list_file_path)

    def nb(self, query):
        return getattr(self.database, 'nb_%s' % NbType(query))

    def valid_size(self):
        return self.database.valid_size

    def valid_length(self):
        return self.database.valid_length

    def same_sizes(self):
        sizes = {}
        for video in self.database.videos:
            if video.exists():
                sizes.setdefault(video.size, []).append(video)
        duplicated_sizes = {size: elements for (size, elements) in sizes.items() if len(elements) > 1}
        if duplicated_sizes:
            utils.print_title('%d DUPLICATE CASE(S)' % len(duplicated_sizes))
            for size in sorted(duplicated_sizes.keys()):
                elements = duplicated_sizes[size]  # type: list
                elements.sort(key=lambda v: v.filename)
                print(size, 'bytes,', len(elements), 'video(s)')
                for video in elements:
                    print('\t%s\t"%s"' % (self.database.get_video_id(video), video.filename))

    def find(self, terms):
        # type: (str) -> None
        terms = {term.strip().lower() for term in terms.split()}
        found = []
        for video in self.database.videos:
            if video.exists() and all(
                    term in video.title.lower() or term in video.filename.path.lower() for term in terms):
                found.append(video)
        print(len(found), 'FOUND', ', '.join(terms))
        found.sort(key=lambda v: v.filename.get_date_modified().time, reverse=True)
        for video in found:
            print('\t%s\t%s\t"%s"' % (
                video.filename.get_date_modified(), self.database.get_video_id(video), video.filename))

    def open(self, video_id):
        video = self.database.get_video_from_id(video_id)
        if video:
            platform_commands = {
                'linux': 'xdg-open',
                'darwin': 'open'
            }
            if sys.platform in platform_commands:
                open_command = platform_commands[sys.platform]
                subprocess.run([open_command, video.filename.path])
                print('Opened', video.filename)
            elif sys.platform == 'win32':
                os.startfile(video.filename.path)
                print('Opened', video.filename)
            else:
                print('Unknown system', sys.platform)
                return
        else:
            print('Not found', video_id)

    def delete(self, video_id):
        video = self.database.get_video_from_id(video_id)
        if video:
            self.database.delete_video(video)
            print('Deleted', video.filename)
        else:
            print('Not found', video_id)

    def clear_not_found(self):
        self.database.remove_videos_not_found(save=True)

    def info(self, video_id):
        video = self.database.get_video_from_id(video_id)
        if video:
            print(video)
        else:
            print('Not found', video_id)

    def rename(self, video_id, new_title):
        if new_title is None or not str(new_title):
            print('No title given')
            return
        new_title = str(new_title)
        video = self.database.get_video_from_id(video_id)  # type: Video
        if video:
            self.database.change_video_file_title(video, new_title)
            new_id = self.database.get_video_id(video)
            print('Renamed', new_id, video.filename)
        else:
            print('Not found', video_id)

    def list(self, field, reverse, page_size, page_number):
        field = FieldType(field)  # type: str
        videos = list(self.database.videos)
        videos.sort(key=lambda video: get_video_info(video, field), reverse=bool(reverse))
        nb_pages = (len(videos) // page_size) + bool(len(videos) % page_size)
        print(len(videos), page_size, page_number, nb_pages)
        selected_videos = videos[(page_size * page_number):(page_size * (page_number + 1))]
        headers = ['No', 'ID', field.upper(), 'Path']
        lines = []
        for i, video in enumerate(selected_videos):
            lines.append(['(%d)' % i, self.database.get_video_id(video), get_video_info(video, field), video.filename])
        return Table(headers=headers, lines=lines)
