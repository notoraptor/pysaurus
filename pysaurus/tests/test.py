from pysaurus.core.database.api import API
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH


def main():
    api = API(TEST_LIST_FILE_PATH, update=False, ensure_miniatures=False, reset=False)
    all_videos = list(api.database.readable.found.with_thumbnails)
    terms = {}
    for video in all_videos:
        for term in video.terms():
            terms.setdefault(term, []).append(video)
    print('Videos:', len(all_videos))
    print('Terms:', len(terms))
    if terms:
        print('Count:')
        for term, cluster in sorted(terms.items(), key=lambda item: (len(item[1]), item[0]), reverse=True):
            print(term, len(cluster))
    all_edges = {}
    print('Edges', len(all_edges))


if __name__ == '__main__':
    main()
