import os
import subprocess
import sys

from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.database import Database
from pysaurus.core.utils import functions as utils
from pysaurus.core.video import Video
from pysaurus.interface.common.table import Table

NbType = utils.enumeration(('entries', 'unreadable', 'not_found', 'valid', 'found', 'thumbnails'))
FieldType = utils.enumeration(Video.PUBLIC_INFO)


def bool_type(mixed):
    if mixed is None:
        return False
    if isinstance(mixed, (bool, int, float)):
        return bool(mixed)
    if isinstance(mixed, str):
        if mixed.lower() == 'true':
            return True
        if not mixed or mixed.lower() == 'false':
            return False
        try:
            return bool(int(mixed))
        except ValueError:
            try:
                return bool(float(mixed))
            except ValueError:
                pass
    return bool(mixed)


class Interface:
    __slots__ = 'database',

    def __init__(self):
        self.database = Interface.load_database()

    @staticmethod
    def load_database():
        # type: () -> Database
        list_file_path = AbsolutePath(os.path.join(utils.package_dir(), '..', '..', '.local', 'test_folder.log'))
        return Database.load_from_list_file(list_file_path)

    def __video(self, video_id):
        # type: (int) -> Video
        video = self.database.get_video_from_id(video_id)
        if not video:
            raise ValueError('Video not found (%d)' % video_id)
        return video

    # ------------------------------------------------------------------------------------------------------------------

    def nb(self, query):
        # type: (str) -> int
        return getattr(self.database, 'nb_%s' % NbType(query))

    def valid_size(self):
        # type: () -> int
        return self.database.valid_size

    def valid_length(self):
        # type: () -> int
        return self.database.valid_length

    def clear_not_found(self):
        # type: () -> None
        self.database.remove_videos_not_found(save=True)

    def open(self, video_id):
        # type: (int) -> bool
        video = self.__video(video_id)
        ok = True
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
            ok = False
        return ok

    def delete(self, video_id):
        # type: (int) -> None
        video = self.__video(video_id)
        self.database.delete_video(video)
        print('Deleted', video.filename)

    def info(self, video_id):
        # type: (int) -> Video
        return self.__video(video_id)

    def rename(self, video_id, new_title):
        # type: (int, str) -> None
        if new_title is None or not str(new_title):
            raise ValueError('No title given')
        new_title = str(new_title)
        video = self.__video(video_id)  # type: Video
        self.database.change_video_file_title(video, new_title)
        new_id = self.database.get_video_id(video)
        print('Renamed', new_id, video.filename)

    def same_sizes(self):
        # type: () -> Table
        sizes = {}
        for video in self.database.valid_videos:
            sizes.setdefault(video.size, []).append(video)
        duplicated_sizes = {size: elements for (size, elements) in sizes.items() if len(elements) > 1}
        if duplicated_sizes:
            headers = ['Size', 'ID', 'Path']
            lines = []
            for size in sorted(duplicated_sizes.keys()):
                elements = duplicated_sizes[size]  # type: list
                elements.sort(key=lambda v: v.filename)
                for video in elements:
                    lines.append([size, self.database.get_video_id(video), video.filename])
                lines.append([])
            return Table(headers=headers, lines=lines)

    def find(self, terms):
        # type: (str) -> Table
        terms = {term.strip().lower() for term in terms.split()}
        found = []
        for video in self.database.valid_videos:
            if all(term in video.title.lower() or term in video.filename.path.lower() for term in terms):
                found.append(video)
        if found:
            found.sort(key=lambda v: v.filename.get_date_modified().time, reverse=True)
            headers = ['Date modified', 'ID', 'Size', 'Path']
            lines = []
            for video in found:
                lines.append([
                    video.filename.get_date_modified(),
                    self.database.get_video_id(video),
                    video.get_size(),
                    video.filename
                ])
            return Table(headers=headers, lines=lines)

    def list(self, field, reverse, page_size, page_number):
        # type: (str, bool, int, int) -> Table
        reverse = bool_type(reverse)
        field = FieldType(field)  # type: str
        videos = list(self.database.valid_videos)
        videos.sort(key=lambda v: v.get(field), reverse=reverse)
        nb_pages = (len(videos) // page_size) + bool(len(videos) % page_size)
        selected_videos = videos[(page_size * page_number):(page_size * (page_number + 1))]
        headers = ['No', 'ID', field.upper(), 'Path']
        lines = []
        for i, video in enumerate(selected_videos):
            lines.append(['(%d)' % i, self.database.get_video_id(video), video.get(field), video.filename])
        return Table(headers=headers, lines=lines)
