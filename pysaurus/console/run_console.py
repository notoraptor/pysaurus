import os

from pysaurus.core import features
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.database import Database


def main(check_thumbnails=True):
    list_file_path = AbsolutePath(os.path.join('..', '..', '..', '.local', 'test_folder.log'))

    # Loading database.
    database = Database(list_file_path)
    database.notify_database_loaded()

    # Update database.
    database.update()

    if check_thumbnails:
        database.ensure_thumbnails()

    features.get_same_sizes(database.videos)
    html = features.get_same_lengths(database.videos)
    if not html:
        print('No same lengths.')
    else:
        with open('same_lengths.html', 'wb') as file:
            file.write(html.encode())
        print(os.path.abspath('same_lengths.html'))
    print('End.')


if __name__ == '__main__':
    main()
