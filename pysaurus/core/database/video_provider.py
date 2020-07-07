"""
select videos
    [] unreadable
        [] not found (x)
        [] found.
    [] readable
        [] not found (x)
        [] found
            [] with thumbnails.
            [] without thumbnails.
from videos select group
    | all
    | grouped by $field ?reverse # len(group) > 1
from group look for videos
    | all
    | search $text $condition
sort by $field ?reverse
"""
import functools
from typing import Optional, Sequence

from pysaurus.core import functions
from pysaurus.core.components import FileSize, Duration
from pysaurus.core.database.database import Database
from pysaurus.core.database.video import Video

UNREADABLE = 'unreadable'
READABLE = 'readable'
NOT_FOUND = 'not_found'
FOUND = 'found'
WITH_THUMBNAILS = 'with_thumbnails'
WITHOUT_THUMBNAILS = 'without_thumbnails'

SOURCE_TREE = {
    UNREADABLE: {
        NOT_FOUND: False,
        FOUND: False
    },
    READABLE: {
        NOT_FOUND: False,
        FOUND: {
            WITH_THUMBNAILS: False,
            WITHOUT_THUMBNAILS: False
        }
    }
}


class GroupDef:

    def __init__(self, field: Optional[str], reverse: Optional[bool]):
        self.field = field
        self.reverse = reverse

    def __bool__(self):
        return bool(self.field)

    @classmethod
    def none(cls):
        return cls(None, None)


class SearchDef:

    def __init__(self, text: Optional[str], cond: Optional[str]):
        self.text = text.strip() if text else None
        self.cond = cond.strip() if cond else None
        if not self.cond or self.cond not in VIDEO_FILTERS:
            self.cond = 'and'

    def __bool__(self):
        return bool(self.text)

    @classmethod
    def none(cls):
        return cls(None, None)


DEFAULT_SOURCE_DEF = (('readable', 'found', 'with_thumbnails'),)
DEFAULT_GROUP_DEF = GroupDef.none()  # str field, bool reverse
DEFAULT_SEARCH_DEF = SearchDef.none()  # str text, str cond
DEFAULT_SORT_DEF = ('-date',)


def _check_source_path(dct, seq, index=0):
    if index < len(seq):
        _check_source_path(dct[seq[index]], seq, index + 1)


def _get_source(inp, seq, index=0):
    if index < len(seq):
        return _get_source(getattr(inp, seq[index]), seq, index + 1)
    else:
        return inp


def filter_exact(video, terms):
    return ' '.join(terms) in ' '.join(video.terms())


def filter_and(video, terms):
    video_terms = video.terms(as_set=True)
    return all(term in video_terms for term in terms)


def filter_or(video, terms):
    video_terms = video.terms(as_set=True)
    return any(term in video_terms for term in terms)


VIDEO_FILTERS = {'exact': filter_exact, 'and': filter_and, 'or': filter_or}


class VideoProvider:
    __slots__ = ('database',
                 'source_def', 'group_def', 'search_def', 'sort_def',
                 'source', 'groups', 'group_id', 'view')

    def __init__(self, database: Database):
        self.database = database

        self.source_def = DEFAULT_SOURCE_DEF
        self.group_def = DEFAULT_GROUP_DEF
        self.search_def = DEFAULT_SEARCH_DEF
        self.sort_def = DEFAULT_SORT_DEF

        self.source = {}
        self.groups = []
        self.group_id = 0
        self.view = []

        self.set_source(self.source_def)

    def set_source(self, paths: Sequence[Sequence[str]]):
        valid_paths = set()
        for path in paths:
            _check_source_path(SOURCE_TREE, path)
            valid_paths.add(tuple(path))
        if valid_paths:
            self.source_def = sorted(valid_paths)
        else:
            self.source_def = DEFAULT_SOURCE_DEF
        self.__update_source()
        self.set_groups(DEFAULT_GROUP_DEF.field, DEFAULT_GROUP_DEF.reverse)

    def set_groups(self, field: Optional[str], reverse: Optional[bool]):
        group_def = GroupDef(field, reverse)
        if group_def:
            grouped_videos = {}
            for video in self.source.values():
                grouped_videos.setdefault(getattr(video, group_def.field), []).append(video)
            groups = {value: videos for value, videos in grouped_videos.items() if len(videos) > 1}
            self.groups = [groups[value] for value in sorted(groups.keys(), reverse=group_def.reverse)]
        else:
            # No group.
            self.groups = [list(self.source.values())]
        self.group_def = group_def
        self.group_id = 0
        if self.groups:
            self.set_search(DEFAULT_SEARCH_DEF.text, DEFAULT_SEARCH_DEF.cond)
        else:
            self.search_def = DEFAULT_SEARCH_DEF
            self.view = []

    def set_search(self, text: Optional[str], cond: Optional[str]):
        search_def = SearchDef(text, cond)
        if search_def:
            terms = functions.string_to_pieces(search_def.text)
            video_filter = VIDEO_FILTERS[search_def.cond]
            self.view = [video for video in self.groups[self.group_id] if video_filter(video, terms)]
        else:
            self.view = self.groups[self.group_id]
        self.search_def = search_def
        self.__sort()

    def set_sort(self, sorting: Sequence[str]):
        self.sort_def = sorting or DEFAULT_SORT_DEF
        self.__sort()

    def get_view_file_size(self):
        return FileSize(sum(video.file_size for video in self.view))

    def get_view_duration(self):
        return Duration(sum(video.raw_microseconds for video in self.view))

    def delete_video(self, index):
        video = self.view[index]
        filename = video.filename
        try:
            self.database.delete_video(video)
            del self.source[filename]
            del self.view[index]
            if self.group_def != (None, None) and len(self.view) < 2:
                self.__delete_current_group()
            return True
        except OSError:
            return False

    def check_group(self):
        if not self.view or not self.group_def:
            return
        field_value = {getattr(video, self.group_def.field) for video in self.view}
        if len(field_value) != 1:
            # Group is not relevant anymore.
            self.__delete_current_group()

    def set_group(self, group_id):
        self.group_id = group_id
        self.set_search(DEFAULT_SEARCH_DEF.text, DEFAULT_SEARCH_DEF.cond)

    def get_group_field_value(self):
        return getattr(self.view[0], self.group_def.field)

    def get_group_def(self):
        if self.group_def:
            return {'field': self.group_def.field, 'reverse': self.group_def.reverse, 'group_id': self.group_id, 'nb_groups': len(self.groups)}
        return None

    def get_search_def(self):
        if self.search_def:
            return {'text': self.search_def.text, 'cond': self.search_def.cond}
        return None

    def get_sorting(self):
        return self.sort_def

    def count(self):
        return len(self.view)

    def count_groups(self):
        return len(self.groups) if self.group_def else 0

    def get_video(self, index):
        return self.view[index]

    def load(self):
        self.sort_def = DEFAULT_SORT_DEF
        self.set_source(self.source_def)

    def get_group_id(self):
        return self.group_id

    def __delete_current_group(self):
        del self.groups[self.group_id]
        if not self.groups:
            return
        if self.group_id == len(self.groups):
            self.group_id -= 1
        self.set_search(DEFAULT_SEARCH_DEF.text, DEFAULT_SEARCH_DEF.cond)

    def __update_source(self):
        source = []
        for path in self.source_def:
            source.extend(_get_source(self.database, path, 0))
        source_dict = {video.filename: video for video in source}
        assert len(source_dict) == len(source)
        self.source = source_dict

    def __sort(self):
        self.view.sort(key=functools.cmp_to_key(lambda v1, v2: Video.compare(v1, v2, self.sort_def)))
