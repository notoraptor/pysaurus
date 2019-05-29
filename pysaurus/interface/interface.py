import os
import subprocess
import sys

from pysaurus.core import utils
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.database import Database


class Interface:
    __slots__ = 'database',

    def __init__(self):
        self.database = Interface.load_database()

    @staticmethod
    def load_database():
        list_file_path = AbsolutePath(os.path.join(utils.package_dir(), '..', '..', '.local', 'test_folder.log'))
        return Database.load_from_list_file(list_file_path)

    def nb_entries(self):
        return self.database.nb_entries

    def nb_unreadable(self):
        return self.database.nb_unreadable

    def nb_not_found(self):
        return self.database.nb_not_found

    def nb_valid(self):
        return self.database.nb_valid

    def nb_found(self):
        return self.database.nb_found

    def nb_thumbnails(self):
        return self.database.nb_thumbnails

    def valid_size(self):
        return self.database.valid_size

    def valid_length(self):
        return self.database.valid_length

    def same_sizes(self):
        sizes = {}
        for video in self.database.videos.values():
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
        for video in self.database.videos.values():
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
            elif sys.platform == 'win32':
                os.startfile(video.filename.path)
            else:
                print('Unknown system', sys.platform)
                return
        else:
            print('Not found', video)