import os
import subprocess
import sys
from typing import Dict, List

import pysaurus.public.api_errors
from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.database.database import Database
from pysaurus.core.database.video import Video
from pysaurus.core.notification import Notifier
from pysaurus.core.utils import functions as utils

NbType = utils.enumeration(('entries', 'unreadable', 'not_found', 'valid', 'found', 'thumbnails'))
FieldType = utils.enumeration(Video.PUBLIC_INFO)


class API:
    __slots__ = 'database',

    def __init__(self, notifier=None):
        self.database = API.load_database(notifier)

    @staticmethod
    def load_database(notifier=None):
        # type: (Notifier) -> Database
        list_file_path = AbsolutePath(os.path.join(utils.package_dir(), '..', '..', '.local', 'test_folder.log'))
        return API.load_from_list_file(list_file_path, notifier)

    @staticmethod
    def load_from_list_file(list_file_path, notifier=None):
        # type: (AbsolutePath, Notifier) -> Database
        database = Database(list_file_path, notifier)
        database.update()
        database.clean_unused_thumbnails()
        database.ensure_thumbnails()
        return database

    def __video(self, video_id):
        # type: (int) -> Video
        video = self.database.get_video_from_id(video_id)
        if not video:
            raise pysaurus.public.api_errors.UnknownVideoID(video_id)
        return video

    # ------------------------------------------------------------------------------------------------------------------

    def nb(self, query):
        # type: (str) -> int
        return getattr(self.database, 'nb_%s' % NbType(query))

    def nb_pages(self, query, page_size):
        if page_size <= 0:
            raise pysaurus.public.api_errors.InvalidPageSize(page_size)
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

    def open(self, video_id):
        # type: (int) -> None
        video = self.__video(video_id)
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
            raise pysaurus.public.api_errors.UnsupportedOS(sys.platform)

    def delete(self, video_id):
        # type: (int) -> None
        video = self.__video(video_id)
        self.database.delete_video(video)

    def rename(self, video_id, new_title):
        # type: (int, str) -> int
        if new_title is None or not str(new_title):
            raise pysaurus.public.api_errors.MissingVideoNewTitle()
        new_title = str(new_title)
        video = self.__video(video_id)  # type: Video
        self.database.change_video_file_title(video, new_title)
        return self.database.get_video_id(video)

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
            raise pysaurus.public.api_errors.InvalidPageSize(page_size)
        field = FieldType(field)  # type: str
        reverse = utils.bool_type(reverse)
        videos = sorted(self.database.valid_videos, key=lambda v: v.get(field), reverse=reverse)
        return videos[(page_size * page_number):(page_size * (page_number + 1))]
