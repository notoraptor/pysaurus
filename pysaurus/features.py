from pysaurus import utils


def get_same_sizes(database: dict):
    sizes = {}
    for video in database.values():
        if video.file_exists:
            sizes.setdefault(video.size, []).append(video)
    duplicated_sizes = {size: elements for (size, elements) in sizes.items() if len(elements) > 1}
    if duplicated_sizes:
        print()
        utils.print_title('%d DUPLICATE CASE(S)' % len(duplicated_sizes))
        for size in sorted(duplicated_sizes.keys()):
            elements = duplicated_sizes[size]  # type: list
            elements.sort(key=lambda v: v.filename)
            print(size, 'bytes,', len(elements), 'video(s)')
            for video in elements:
                print('\t"%s"' % video.filename)


def find(database: dict, term: str):
    term = term.lower()
    found = []
    for video in database.values():
        if term in video.filename.title.lower() or (video.title and term in video.title.lower()):
            found.append(video)
    print(len(found), 'FOUND', term)
    found.sort(key=lambda v: v.filename)
    for video in found:
        print('\t"%s"' % video.filename)
