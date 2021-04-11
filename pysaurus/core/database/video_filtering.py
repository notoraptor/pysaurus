UNREADABLE = "unreadable"
READABLE = "readable"
NOT_FOUND = "not_found"
FOUND = "found"
WITH_THUMBNAILS = "with_thumbnails"
WITHOUT_THUMBNAILS = "without_thumbnails"
SOURCE_TREE = {
    UNREADABLE: {NOT_FOUND: False, FOUND: False},
    READABLE: {
        NOT_FOUND: {WITH_THUMBNAILS: False, WITHOUT_THUMBNAILS: False},
        FOUND: {WITH_THUMBNAILS: False, WITHOUT_THUMBNAILS: False},
    },
}


class TreeUtils:
    @staticmethod
    def collect_full_paths(tree: dict, collection: list, prefix=()):
        if not isinstance(prefix, list):
            prefix = list(prefix)
        if tree:
            for key, value in tree.items():
                entry_name = prefix + [key]
                TreeUtils.collect_full_paths(value, collection, entry_name)
        elif prefix:
            collection.append(prefix)

    @staticmethod
    def check_source_path(dct, seq, index=0):
        if index < len(seq):
            TreeUtils.check_source_path(dct[seq[index]], seq, index + 1)

    @staticmethod
    def get_source_from_dict(inp, seq, index=0):
        if index < len(seq):
            return TreeUtils.get_source_from_dict(inp[seq[index]], seq, index + 1)
        else:
            return inp


def get_usable_source_tree():
    tree = SOURCE_TREE.copy()
    del tree["unreadable"]
    return tree


USABLE_SOURCE_TREE = get_usable_source_tree()
