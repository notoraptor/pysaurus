import os
import subprocess
import sys
from typing import Dict, List

from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.database.database import Database
from pysaurus.core.database.video import Video
from pysaurus.core.function_parsing.function_parser import FunctionParser
from pysaurus.core.notification import Notifier
from pysaurus.core.utils import functions as utils
from pysaurus.core.utils.classes import Table
from pysaurus.core.utils.functions import bool_type
from pysaurus.public import api_errors

NbType = utils.enumeration(('entries', 'unreadable', 'not_found', 'valid', 'found', 'thumbnails'))
FieldType = utils.enumeration(Video.TABLE_FIELDS)


class API:
    __slots__ = 'database',

    def __init__(self, notifier=None):
        self.database = API.load_database(notifier)

    @staticmethod
    def load_database(notifier=None):
        # type: (Notifier) -> Database
        list_file_path = AbsolutePath(os.path.join(utils.package_dir(), '..', '..', '.local', 'test_folder.log'))
        database = Database(list_file_path, notifier)
        database.update()
        database.clean_unused_thumbnails()
        database.ensure_thumbnails()
        return database

    def __video(self, video_id):
        # type: (int) -> Video
        video = self.database.get_video_from_id(video_id)
        if not video:
            raise api_errors.UnknownVideoID(video_id)
        return video

    def __video_from_filename(self, filename):
        video = self.database.get_video_from_filename(filename)
        if not video:
            raise api_errors.UnknownVideoFilename()
        return video

    def export_api(self, function_parser):
        # type: (FunctionParser) -> None
        function_parser.add(self.nb, arguments={'query': NbType})
        function_parser.add(self.nb_pages, arguments={'query': NbType, 'page_size': int})
        function_parser.add(self.valid_size)
        function_parser.add(self.valid_length)
        function_parser.add(self.clear_not_found)
        function_parser.add(self.info, arguments={'video_id': int})
        function_parser.add(self.image, arguments={'video_id': int})
        function_parser.add(self.image_filename, arguments={'filename': str})
        function_parser.add(self.clip, arguments={'video_id': int, 'start': int, 'length': int})
        function_parser.add(self.clip_filename, arguments={'filename': str, 'start': int, 'length': int})
        function_parser.add(self.open, arguments={'video_id': int})
        function_parser.add(self.open_filename, arguments={'filename': str})
        function_parser.add(self.delete, arguments={'video_id': int})
        function_parser.add(self.delete_filename, arguments={'filename': str})
        function_parser.add(self.rename, arguments={'video_id': int, 'new_title': str})
        function_parser.add(self.rename_filename, arguments={'filename': str, 'new_title': str})
        function_parser.add(self.same_sizes)
        function_parser.add(self.find, arguments={'terms': str})
        function_parser.add(self.list, arguments={
            'field': FieldType,
            'reverse': bool_type,
            'page_size': int,
            'page_number': int
        })
        function_parser.add(self.videos)
        function_parser.add(self.database_info, arguments={'page_size': int})

    def __open(self, video):
        # type: (Video) -> None
        platform_commands = {
            'linux': 'xdg-open',
            'darwin': 'open'
        }
        if sys.platform in platform_commands:
            open_command = platform_commands[sys.platform]
            subprocess.run([open_command, video.filename.path])
        elif sys.platform == 'win32':
            os.startfile(video.filename.path)
        else:
            raise api_errors.UnsupportedOS(sys.platform)

    # ------------------------------------------------------------------------------------------------------------------

    def nb(self, query):
        # type: (str) -> int
        return getattr(self.database, 'nb_%s' % NbType(query))

    def nb_pages(self, query, page_size):
        # type: (str, int) -> int
        if page_size <= 0:
            raise api_errors.InvalidPageSize(page_size)
        count = self.nb(query)
        return (count // page_size) + bool(count % page_size)

    def valid_size(self):
        # type: () -> int
        return self.database.valid_size

    def valid_length(self):
        # type: () -> int
        return self.database.valid_length

    def clear_not_found(self):
        # type: () -> None
        self.database.remove_videos_not_found(save=True)

    def info(self, video_id):
        # type: (int) -> Video
        return self.__video(video_id)

    def image(self, video_id):
        # type: (int) -> str
        video = self.__video(video_id)
        return video.thumbnail_to_base64(self.database.folder)

    def image_filename(self, filename):
        # type: (str) -> str
        return self.__video_from_filename(filename).thumbnail_to_base64(self.database.folder)

    def clip(self, video_id, start, length):
        # type: (int, int, int) -> str
        return self.__video(video_id).clip_to_base64(start, length)

    def open(self, video_id):
        # type: (int) -> None
        return self.__open(self.__video(video_id))

    def clip_filename(self, filename, start, length):
        # type: (str, int, int) -> str
        return self.__video_from_filename(filename).clip_to_base64(start, length)

    def open_filename(self, filename):
        # type: (str) -> None
        return self.__open(self.__video_from_filename(filename))

    def delete(self, video_id):
        # type: (int) -> int
        video = self.__video(video_id)
        self.database.delete_video(video)
        return self.database.nb_valid

    def delete_filename(self, filename):
        # type: (str) -> int
        video = self.__video_from_filename(filename)
        self.database.delete_video(video)
        return self.database.nb_valid

    def rename(self, video_id, new_title):
        # type: (int, str) -> int
        if new_title is None or not str(new_title):
            raise api_errors.MissingVideoNewTitle()
        new_title = str(new_title)
        video = self.__video(video_id)  # type: Video
        self.database.change_video_file_title(video, new_title)
        return self.database.get_video_id(video)

    def rename_filename(self, filename, new_title):
        # type: (str, str) -> (str, str)
        if new_title is None or not str(new_title):
            raise api_errors.MissingVideoNewTitle()
        new_title = str(new_title)
        video = self.__video_from_filename(filename)  # type: Video
        self.database.change_video_file_title(video, new_title)
        return video.filename.path, video.filename.title

    def same_sizes(self):
        # type: () -> Dict[int, List[Video]]
        sizes = {}
        for video in self.database.valid_videos:
            sizes.setdefault(video.size, []).append(video)
        return {size: elements for (size, elements) in sizes.items() if len(elements) > 1}

    def find(self, terms):
        # type: (str) -> List[Video]
        terms = {term.strip().lower() for term in terms.split()}
        return [video for video in self.database.valid_videos
                if all(term in video.title.lower() or term in video.filename.path.lower() for term in terms)]

    def list(self, field, reverse, page_size, page_number):
        # type: (str, bool, int, int) -> List[Video]
        if page_size <= 0:
            raise api_errors.InvalidPageSize(page_size)
        field = FieldType(field)  # type: str
        reverse = utils.bool_type(reverse)
        videos = sorted(self.database.valid_videos, key=lambda v: v.get(field), reverse=reverse)
        return videos[(page_size * page_number):(page_size * (page_number + 1))]

    def videos(self):
        # type: () -> Table
        return Table(headers=Video.TABLE_FIELDS, lines=[video.to_table_line() for video in self.database.valid_videos])

    # ------------------------------------------------------------------------------------------------------------------
    # Unstable APIs.
    # ------------------------------------------------------------------------------------------------------------------

    def database_info(self, page_size):
        return {
            'count': self.nb('valid'),
            'nbPages': self.nb_pages('valid', page_size),
            'size': self.database.valid_size,
            'duration': self.database.valid_length
        }
