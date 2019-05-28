import os
import subprocess
import sys

from pysaurus.core import features
from pysaurus.core import utils
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.database import Database
from pysaurus.interface.console.input_interface import InputInterface


class Console(InputInterface):
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
        features.same_sizes(self.database)

    def find(self, terms):
        features.find(self.database, {term.strip() for term in terms.split()})

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

    # ------------------------------------------------------------------------------------------------------------------

    @staticmethod
    def load_database():
        list_file_path = AbsolutePath(os.path.join(utils.package_dir(), '..', '..', '.local', 'test_folder.log'))
        return Database.load_from_list_file(list_file_path)

    def __init__(self):
        super(Console, self).__init__()
        self.database = Console.load_database()
        self.add_function(self.nb_entries, 'nb_entries')
        self.add_function(self.nb_unreadable, 'nb_unreadable')
        self.add_function(self.nb_not_found, 'nb_not_found')
        self.add_function(self.nb_valid, 'nb_valid')
        self.add_function(self.nb_found, 'nb_found')
        self.add_function(self.nb_thumbnails, 'nb_thumbnails')
        self.add_function(self.valid_size, 'valid_size')
        self.add_function(self.valid_length, 'valid_length')
        self.add_function(self.same_sizes, 'same_sizes')
        self.add_function(self.find, 'find', {'terms': str})
        self.add_function(self.open, 'open', {'video_id': int})


def main():
    Console().run('[CONSOLE INTERFACE]')
    print('End.')


if __name__ == '__main__':
    main()
