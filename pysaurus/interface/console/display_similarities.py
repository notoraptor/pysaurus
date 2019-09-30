import sys

import ujson as json

from pysaurus.core.database.api import API
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH


def main():
    if len(sys.argv) != 2:
        print(sys.argv)
        return
    with open(sys.argv[1]) as file:
        similarities = json.load(file)
    print('LOADING DATABASE')
    database = API.load_database(TEST_LIST_FILE_PATH)
    with open('output.tsv', 'wb') as file:
        for group_id, group in enumerate(similarities):
            videos = []
            for file_name in sorted(group):
                video = database.get_video_from_filename(file_name)
                assert video
                videos.append(video)
            videos.sort(key=lambda v: v.size)
            file.write(('%d\n' % (group_id + 1)).encode())
            for video in videos:
                file.write(('\t%s\t"%s"\n' % (str(video.get_size()).ljust(10), video.filename)).encode())


if __name__ == '__main__':
    main()
