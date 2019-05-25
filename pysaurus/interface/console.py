import os

from pysaurus.core import features
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.database import Database


def main():
    list_file_path = AbsolutePath(os.path.join('..', '..', '..', '.local', 'test_folder.log'))

    # Loading database.
    database = Database.load_from_list_file(list_file_path)
    # database.remove_videos_not_found(save=True)
    features.get_same_sizes(database.videos)
    # html = features.get_same_lengths(database.videos)
    # if not html:
    #     print('No same lengths.')
    # else:
    #     with open('same_lengths.html', 'wb') as file:
    #         file.write(html.encode())
    #     print(os.path.abspath('same_lengths.html'))
    print('End.')


if __name__ == '__main__':
    main()
