"""
Select sources
Select group
Search
Sort
"""
import functools
import random
from abc import abstractmethod
from copy import copy
from typing import Optional, Sequence, Dict, Generic, List, Callable, Any, TypeVar, Type, Union, Iterable, Set

from pysaurus.core import functions
from pysaurus.core.classes import ToDict
from pysaurus.core.components import FileSize, Duration, AbsolutePath
from pysaurus.core.database.database import Database
from pysaurus.core.database.video import Video

T = TypeVar('T')
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
        NOT_FOUND: {
            WITH_THUMBNAILS: False,
            WITHOUT_THUMBNAILS: False,
        },
        FOUND: {
            WITH_THUMBNAILS: False,
            WITHOUT_THUMBNAILS: False
        }
    }
}


def deep_equals(value, other):
    value_type = type(value)
    assert value_type is type(other), (value_type, type(other))
    if value_type in (bool, int, float, str):
        return value == other
    if value_type in (list, tuple, set):
        if len(value) != len(other):
            return False
        if value_type is set:
            value = sorted(value)
            other = sorted(other)
        return all(deep_equals(value[i], other[i]) for i in range(len(value)))
    if value_type is dict:
        if len(value) != len(other):
            return False
        return all(key in other and deep_equals(value[key], other[key]) for key in value)
    return value == other


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
    def get_source_from_object(inp, seq, index=0):
        if index < len(seq):
            return TreeUtils.get_source_from_object(getattr(inp, seq[index]), seq, index + 1)
        else:
            return inp

    @staticmethod
    def get_source_from_dict(inp, seq, index=0):
        if index < len(seq):
            return TreeUtils.get_source_from_dict(inp[seq[index]], seq, index + 1)
        else:
            return inp


class NegativeComparator:
    __slots__ = 'value',

    def __init__(self, value):
        self.value = value

    def __lt__(self, other):
        return other.value < self.value


class GroupDef(ToDict):
    __slots__ = 'field', 'sorting', 'reverse', 'allow_singletons', 'allow_multiple'
    __none__ = True

    FIELD = "field"
    LENGTH = "length"
    COUNT = "count"

    def __init__(self,
                 field: Optional[str],
                 sorting: Optional[str] = 'field',
                 reverse: Optional[bool] = False,
                 allow_singletons: Optional[bool] = False,
                 allow_multiple: Optional[bool] = True):
        self.field = field.strip() if field else None
        self.sorting = sorting.strip() if sorting else None
        self.reverse = bool(reverse)
        self.allow_singletons = bool(allow_singletons)
        self.allow_multiple = bool(allow_multiple)
        assert self.sorting in (self.FIELD, self.LENGTH, self.COUNT)

    def __bool__(self):
        return bool(self.field)

    def __eq__(self, other):
        return (self.field == other.field
                and self.sorting == other.sorting
                and self.reverse == other.reverse
                and self.allow_singletons == other.allow_singletons
                and self.allow_multiple == other.allow_multiple)

    def copy(self, field=None, sorting=None, reverse=None, allow_singletons=None, allow_multiple=None):
        field = field if field is not None else self.field
        sorting = sorting if sorting is not None else self.sorting
        reverse = reverse if reverse is not None else self.reverse
        allow_singletons = allow_singletons if allow_singletons is not None else self.allow_singletons
        allow_multiple = allow_multiple if allow_multiple is not None else self.allow_multiple
        return GroupDef(field, sorting, reverse, allow_singletons, allow_multiple)

    def sort(self, groups):
        # type: (List[Group]) -> List[Group]
        return self.sort_groups(groups, self.field, self.sorting, self.reverse)

    @classmethod
    def sort_groups(cls, groups, field, sorting='field', reverse=False):
        # type: (List[Group], str, str, bool) -> List[Group]
        none_group = None
        other_groups = []
        for group in groups:
            if group.field_value is None:
                assert none_group is None
                none_group = group
            else:
                other_groups.append(group)
        field_comparator = cls.generate_comparator(field, reverse)
        if sorting == cls.FIELD:
            key = lambda group: field_comparator(group.field_value)
        elif sorting == cls.COUNT:
            key = lambda group: (
                cls.make_comparable_number(len(group.videos), reverse),
            ) + field_comparator(group.field_value)
        else:
            assert sorting == cls.LENGTH
            key = lambda group: (
                cls.make_comparable_number(len(str(group.field_value)), reverse),
            ) + field_comparator(group.field_value)
        other_groups.sort(key=key)
        return ([none_group] + other_groups) if none_group else other_groups

    @classmethod
    def none(cls):
        return cls(None)

    @classmethod
    def make_comparable_number(cls, value: Union[int, float], reverse: bool):
        return -value if reverse else value

    @classmethod
    def generate_comparator(cls, field, reverse, remaining_tuple=()):
        if field in Video.STRING_FIELDS:
            if reverse:
                return lambda value: (NegativeComparator(value.lower()), NegativeComparator(value)) + remaining_tuple
            else:
                return lambda value: (value.lower(), NegativeComparator(value)) + remaining_tuple
        elif reverse:
            return lambda value: (NegativeComparator(value),) + remaining_tuple
        else:
            return lambda value: (value,) + remaining_tuple


class SearchDef(ToDict):
    __slots__ = 'text', 'cond'
    __none__ = True

    def __init__(self, text: Optional[str], cond: Optional[str]):
        self.text = text.strip() if text else None
        self.cond = cond.strip() if cond else None
        if not self.cond or not hasattr(Video, 'has_terms_%s' % self.cond):
            self.cond = 'and'

    def __bool__(self):
        return bool(self.text)

    def __eq__(self, other):
        return self.text == other.text and self.cond == other.cond

    @classmethod
    def none(cls):
        return cls(None, None)


class Group:
    __slots__ = 'field_value', 'videos'

    def __init__(self, field_value, videos):
        self.field_value = field_value
        self.videos = VideoArray(videos)

    def __str__(self):
        return 'Group(%s, %s)' % (self.field_value, len(self.videos))


class LookupArray(Generic[T]):
    __slots__ = '__type', '__content', '__table', '__key_fn'

    def __init__(self, element_type, content: Sequence = (), key: callable = None):
        self.__type = element_type  # type: Type
        self.__content = []  # type: List[T]
        self.__table = {}  # type: Dict[Any, int]
        self.__key_fn = key if callable(key) else lambda value: value  # type: Callable[[T], Any]
        for element in content:
            self.append(element)

    def __str__(self):
        return '%s<%s>%s' % (type(self).__name__, self.__type.__name__, self.__content)

    def __len__(self):
        return len(self.__content)

    def __getitem__(self, item):
        return copy(self.__content[item])

    def __iter__(self):
        return self.__content.__iter__()

    def __reversed__(self):
        return self.__content.__reversed__()

    def __contains__(self, value: T):
        return isinstance(value, self.__type) and self.__key_fn(value) in self.__table

    def __check_type(self, value):
        assert value is None or isinstance(value, self.__type), value

    def extend(self, iterable):
        for element in iterable:
            self.append(element)

    def append(self, value: T):
        self.__check_type(value)
        self.__content.append(value)
        self.__table[self.__key_fn(value)] = len(self.__content) - 1

    def pop(self, index: int):
        if index < 0:
            index = len(self.__content) + index
        value = self.__content.pop(index)
        assert index == self.__table.pop(self.__key_fn(value))
        for i in range(index, len(self.__content)):
            self.__table[self.__key_fn(self.__content[i])] = i
        return value

    def remove(self, value: T):
        self.__check_type(value)
        self.pop(self.__table[self.__key_fn(value)])

    def lookup(self, key) -> T:
        value = self.__content[self.__table[key]]
        assert key == self.__key_fn(value)
        return value

    def lookup_index(self, key):
        return self.__table[key]

    def contains_key(self, key):
        return key in self.__table

    def keys(self):
        return self.__table.keys()

    def new(self, content=()):
        return LookupArray(self.__type, content, self.__key_fn)

    def clear(self):
        self.__content.clear()
        self.__table.clear()


class VideoArray(LookupArray[Video]):
    __slots__ = ()

    def __init__(self, content=()):
        super().__init__(Video, content, lambda video: video.filename)


class GroupArray(LookupArray[Group]):
    __slots__ = ('field',)

    def __init__(self, field: str, content=()):
        super().__init__(Group, content, lambda group: group.field_value)
        self.field = field


class Layer:
    __slots__ = ('__sub_layer', 'parent', '__args', '__to_update', '__filtered', '__data', 'database')
    __props__ = ()

    def __init__(self, database: Database):
        self.__args = {}
        self.__sub_layer = None  # type: Optional[Layer]
        self.__to_update = False
        self.__filtered = None
        self.__data = None
        self.parent = None  # type: Optional[Layer]
        self.database = database
        self.reset_parameters()

    def get_root(self):
        layer = self
        while layer.parent is not None:
            layer = layer.parent
        return layer

    def __log(self, *args, **kwargs):
        print('%s/' % type(self).__name__, *args, **kwargs)

    def set_parent(self, parent):
        self.parent = parent

    def set_sub_layer(self, sub_layer):
        self.__sub_layer = sub_layer
        sub_layer.set_parent(self)
        self.__log('sub-filter', None if self.__sub_layer is None else 'set')

    def _set_parameters(self, **kwargs):
        for key in kwargs:
            assert key in self.__props__, (key, self.__props__)
            if key not in self.__args or not deep_equals(kwargs[key], self.__args[key]):
                self.__to_update = True
                self.__args[key] = kwargs[key]
                self.__log('set parameter', key, kwargs[key])

    @property
    def _cache(self):
        return self.__filtered

    def set_data(self, data):
        self.__to_update = True
        self.__data = data
        self.__log('data', None if self.__data is None else 'set %s' % type(data).__name__)

    def request_update(self):
        self.__to_update = True
        self.__log('update forced')

    def requires_update(self):
        return self.__to_update

    def get_parameter(self, key):
        return self.__args[key]

    def run(self):
        if not self.__data:
            self.__log('run no data')
            return ()
        if self.__to_update:
            self.__filtered = self.filter(self.__data)
            self.__to_update = False
            self.__log('run')
            if self.__sub_layer:
                self.__sub_layer.set_data(self.__filtered)
                return self.__sub_layer.run()
            else:
                return self.__filtered
        elif self.__sub_layer:
            if self.__sub_layer.requires_update():
                self.__sub_layer.set_data(self.__filtered)
            return self.__sub_layer.run()
        else:
            return self.__filtered

    def delete_video(self, video):
        self.remove_from_cache(self.__filtered, video)
        self.__log('delete', video.filename)
        if self.__sub_layer:
            self.__sub_layer.delete_video(video)

    @abstractmethod
    def reset_parameters(self):
        raise NotImplementedError()

    @abstractmethod
    def filter(self, data):
        raise NotImplementedError()

    @abstractmethod
    def remove_from_cache(self, cache, video: Video):
        raise NotImplementedError


class SourceLayer(Layer):
    __slots__ = ('index',)
    __props__ = ('sources',)
    _cache: Dict[AbsolutePath, Video]
    DEFAULT_SOURCE_DEF = [('readable',)]

    def __init__(self, database):
        super().__init__(database)
        self.index = {}  # type: Dict[str, Set[Video]]

    def set_sources(self, paths: Sequence[Sequence[str]]):
        valid_paths = set()
        for path in paths:
            path = tuple(path)
            if path not in valid_paths:
                TreeUtils.check_source_path(SOURCE_TREE, path)
                valid_paths.add(path)
        if valid_paths:
            self._set_parameters(sources=sorted(valid_paths))

    def get_sources(self):
        return self.get_parameter('sources')

    def reset_parameters(self):
        self.set_sources(self.DEFAULT_SOURCE_DEF)

    def filter(self, database: Database) -> Dict[AbsolutePath, Video]:
        source = []
        for path in self.get_sources():
            source.extend(TreeUtils.get_source_from_object(database, path, 0))
        source_dict = {video.filename: video for video in source}
        assert len(source_dict) == len(source), (len(source_dict), len(source))
        self.index = self.__index_videos(source)
        return source_dict

    def remove_from_cache(self, cache: Dict[AbsolutePath, Video], video: Video):
        assert video.filename in cache, len(cache)
        for term in video.terms(as_set=True):
            assert video in self.index[term], len(self.index[term])
            self.index[term].remove(video)
            if not self.index[term]:
                del self.index[term]
        del cache[video.filename]

    def count_videos(self):
        return len(self._cache)

    def videos(self):
        return self._cache.values()

    @classmethod
    def __index_videos(cls, videos: Iterable[Video]) -> Dict[str, Set[Video]]:
        term_to_videos = {}
        for video in videos:
            for term in video.terms():
                term_to_videos.setdefault(term, set()).add(video)
        return term_to_videos


class GroupingLayer(Layer):
    __slots__ = ()
    __props__ = ('grouping',)
    _cache: GroupArray
    DEFAULT_GROUP_DEF = GroupDef.none()  # str field, bool reverse

    def set_grouping(self, *,
                     field: Optional[str] = None,
                     sorting: Optional[str] = None,
                     reverse: Optional[bool] = None,
                     allow_singletons: Optional[bool] = None,
                     allow_multiple: Optional[bool] = None):
        self._set_parameters(grouping=self.get_grouping().copy(
            field, sorting, reverse, allow_singletons, allow_multiple))

    def get_grouping(self) -> GroupDef:
        return self.get_parameter('grouping')

    def reset_parameters(self):
        self._set_parameters(grouping=self.DEFAULT_GROUP_DEF)

    def filter(self, data: Dict[AbsolutePath, Video]) -> GroupArray:
        group_def = self.get_grouping()
        groups = []
        if not group_def:
            groups.append(Group(None, list(data.values())))
        elif group_def.allow_singletons or group_def.allow_multiple:
            grouped_videos = {}
            if group_def.field[0] == ':':
                field = group_def.field[1:]
                prop_type = self.database.get_prop_type(field)
                if prop_type.multiple:
                    for video in data.values():
                        values = video.properties.get(field, None) or [None]
                        for value in values:
                            grouped_videos.setdefault(value, []).append(video)
                else:
                    for video in data.values():
                        grouped_videos.setdefault(video.properties.get(field, prop_type.default), []).append(video)
            else:
                for video in data.values():
                    grouped_videos.setdefault(getattr(video, group_def.field), []).append(video)
            for field_value, videos in grouped_videos.items():
                if (field_value is None
                        or (group_def.allow_singletons and len(videos) == 1)
                        or (group_def.allow_multiple and len(videos) > 1)):
                    groups.append(Group(field_value, videos))
            groups = group_def.sort(groups)
        return GroupArray(group_def.field, groups)

    def remove_from_cache(self, cache: GroupArray, video: Video):
        groups = []
        if len(cache) == 1 and cache[0].field_value is None:
            groups.append(cache[0])
        else:
            field_name = self.get_grouping().field
            if field_name[0] == ':':
                prop_type = self.database.get_prop_type(field_name[1:])
                if prop_type.multiple:
                    field_value = video.properties.get(field_name[1:], [None])
                else:
                    field_value = [video.properties.get(field_name[1:], prop_type.default)]
            else:
                field_value = [getattr(video, self.get_grouping().field)]
            for value in field_value:
                if cache.contains_key(value):
                    groups.append(cache.lookup(value))
        for group in groups:
            if video in group.videos:
                group.videos.remove(video)
                if not group.videos or (not self.get_grouping().allow_singletons and len(group.videos) == 1):
                    group.videos.clear()
                    cache.remove(group)


class ClassifierLayer(Layer):
    __slots__ = ()
    __props__ = 'path',
    _cache: GroupArray

    def set_path(self, path: list):
        self._set_parameters(path=path)

    def get_path(self) -> list:
        return self.get_parameter('path')

    def reset_parameters(self):
        self._set_parameters(path=[])

    def classify_videos(self, videos: Iterable[Video], prop_name: str, values: List) -> GroupArray:
        classes = {}
        for video in videos:
            for value in video.properties.get(prop_name, []):
                classes.setdefault(value, []).append(video)
        if values:
            latest_value = values[-1]
            for value in values[:-1]:
                classes.pop(value)
            latest_group = Group(None, classes.pop(latest_value))
            other_groups = [Group(field_value, group_videos) for field_value, group_videos in classes.items()]
            groups = other_groups if latest_group is None else [latest_group] + other_groups
        else:
            groups = [Group(field_value, group_videos) for field_value, group_videos in classes.items()]
        field = ':' + prop_name
        if self.parent and isinstance(self.parent, GroupingLayer):
            return GroupArray(field, self.parent.get_grouping().sort(groups))
        else:
            return GroupArray(field, GroupDef.sort_groups(groups, field))

    def filter(self, data: GroupArray) -> GroupArray:
        if data.field is None or data.field[0] != ':':
            return data
        prop_name = data.field[1:]
        if not self.database.get_prop_type(prop_name).multiple:
            return data
        path = self.get_path()
        if not path:
            return data
        videos = set(data.lookup(path[0]).videos)
        for value in path[1:]:
            videos &= set(data.lookup(value).videos)
        assert videos
        return self.classify_videos(videos, prop_name, path)

    def remove_from_cache(self, cache: GroupArray, video: Video):
        groups = []
        if len(cache) == 1 and cache[0].field_value is None:
            groups.append(cache[0])
        else:
            field_name = cache.field
            if field_name[0] == ':':
                prop_type = self.database.get_prop_type(field_name[1:])
                if prop_type.multiple:
                    field_value = video.properties.get(field_name[1:], [None])
                else:
                    field_value = [video.properties.get(field_name[1:], prop_type.default)]
            else:
                field_value = [getattr(video, cache.field)]
            for value in field_value:
                if cache.contains_key(value):
                    groups.append(cache.lookup(value))
        for group in groups:
            if video in group.videos:
                group.videos.remove(video)
                if not group.videos:
                    group.videos.clear()
                    cache.remove(group)

    def get_group_value(self, index):
        return self._cache[index].field_value

    def count_groups(self):
        return len(self._cache)

    def get_stats(self):
        field = self._cache.field
        if field[0] == ':':
            converter = functions.identity
        else:
            converter = str
        return [{'value': converter(g.field_value), 'count': len(g.videos)} for g in self._cache]


class GroupLayer(Layer):
    __slots__ = ()
    __props__ = ('group_id',)

    _cache: Group

    def set_group_id(self, group_id: int):
        if group_id < 0:
            group_id = 0
        self._set_parameters(group_id=group_id)

    def get_group_id(self) -> int:
        return self.get_parameter('group_id')

    def _clip_group_id(self, nb_groups):
        group_id = self.get_group_id()
        if group_id >= nb_groups:
            group_id = nb_groups - 1
            self.set_group_id(group_id)
        return self.get_group_id()

    def reset_parameters(self):
        self.set_group_id(0)

    def filter(self, data: Sequence[Group]) -> Group:
        return data[self._clip_group_id(len(data))]

    def remove_from_cache(self, cache: Group, video: Video):
        if video in cache.videos:
            cache.videos.remove(video)
        if not cache.videos:
            self.request_update()

    def get_field_value(self):
        return self._cache.field_value


class SearchLayer(Layer):
    __slots__ = ()
    __props__ = ('search',)
    DEFAULT_SEARCH_DEF = SearchDef.none()  # str text, str cond

    def set_search(self, text: Optional[str], cond: Optional[str]):
        self._set_parameters(search=SearchDef(text, cond))

    def get_search(self) -> SearchDef:
        return self.get_parameter('search')

    def reset_parameters(self):
        self._set_parameters(search=self.DEFAULT_SEARCH_DEF)

    def filter(self, data: Group) -> VideoArray:
        search_def = self.get_search()
        if search_def:
            root = self.get_root()
            if isinstance(root, SourceLayer):
                return self.__filter_from_root_layer(search_def, root, data)
            return self.__filter_from_videos(search_def, data)
        return data.videos

    @classmethod
    def __filter_from_videos(cls, search_def: SearchDef, data: Group) -> VideoArray:
        terms = functions.string_to_pieces(search_def.text)
        video_filter = getattr(Video, 'has_terms_%s' % search_def.cond)
        return data.videos.new(video for video in data.videos if video_filter(video, terms))

    @classmethod
    def __filter_from_root_layer(cls, search_def: SearchDef, source_layer: SourceLayer, data: Group) -> VideoArray:
        assert search_def.cond in ('exact', 'and', 'or')
        term_to_videos = source_layer.index
        terms = functions.string_to_pieces(search_def.text)
        if search_def.cond == 'exact':
            selection_and = set(data.videos)
            for term in terms:
                selection_and &= term_to_videos.get(term, set())
            video_filter = getattr(Video, 'has_terms_%s' % search_def.cond)
            selection = data.videos.new(video for video in selection_and if video_filter(video, terms))
        elif search_def.cond == 'and':
            selection = set(data.videos)
            for term in terms:
                selection &= term_to_videos.get(term, set())
        else:  # search_def.cond == 'or'
            selection = set(term_to_videos.get(terms[0], set()))
            for term in terms[1:]:
                selection |= term_to_videos.get(term, set())
            selection &= set(data.videos)
        return data.videos.new(selection)

    def remove_from_cache(self, cache: VideoArray, video: Video):
        if video in cache:
            cache.remove(video)


class SortLayer(Layer):
    __slots__ = ()
    __props__ = ('sorting',)
    DEFAULT_SORT_DEF = ['-date']

    def set_sorting(self, sorting: Sequence[str]):
        self._set_parameters(sorting=list(sorting) if sorting else self.DEFAULT_SORT_DEF)

    def get_sorting(self):
        return self.get_parameter('sorting')

    def reset_parameters(self):
        self.set_sorting(self.DEFAULT_SORT_DEF)

    def filter(self, data: Sequence[Video]) -> VideoArray:
        return VideoArray(sorted(data, key=functools.cmp_to_key(
            lambda v1, v2: Video.compare(v1, v2, self.get_sorting()))))

    def remove_from_cache(self, cache: VideoArray, video: Video):
        if video in cache:
            cache.remove(video)


class VideoProvider:
    __slots__ = ('database', '__source_layer', 'grouping_layer', 'classifier_layer', 'group_layer', 'search_layer',
                 'sort_layer', 'view')

    def __init__(self, database: Database):
        self.database = database
        self.view = []

        self.__source_layer = SourceLayer(database)
        self.grouping_layer = GroupingLayer(database)
        self.classifier_layer = ClassifierLayer(database)
        self.group_layer = GroupLayer(database)
        self.search_layer = SearchLayer(database)
        self.sort_layer = SortLayer(database)

        self.__source_layer.set_sub_layer(self.grouping_layer)
        self.grouping_layer.set_sub_layer(self.classifier_layer)
        self.classifier_layer.set_sub_layer(self.group_layer)
        self.group_layer.set_sub_layer(self.search_layer)
        self.search_layer.set_sub_layer(self.sort_layer)

        ##
        # if self.database.has_prop_type('category'):
        #     prop_category = self.database.get_prop_type('category')
        #     if prop_category.type is str and prop_category.multiple:
        #         self.grouping_layer.set_grouping(
        #             field=':category',
        #             sorting='field',
        #             reverse=False,
        #             allow_singletons=True,
        #             allow_multiple=True
        #         )
        ##

        self.__source_layer.set_data(self.database)
        self.view = self.__source_layer.run()
        assert isinstance(self.view, VideoArray)

    def set_source(self, paths: Sequence[Sequence[str]]):
        self.__source_layer.set_sources(paths)
        self.view = self.__source_layer.run()

    def set_groups(self,
                   field: Optional[str],
                   sorting: Optional[str] = None,
                   reverse: Optional[bool] = None,
                   allow_singletons: Optional[bool] = None,
                   allow_multiple: Optional[bool] = None):
        self.grouping_layer.set_grouping(field=field,
                                         sorting=sorting,
                                         reverse=reverse,
                                         allow_singletons=allow_singletons,
                                         allow_multiple=allow_multiple)
        self.group_layer.set_group_id(0)
        self.search_layer.reset_parameters()
        self.view = self.__source_layer.run()

    def set_search(self, text: Optional[str], cond: Optional[str]):
        self.search_layer.set_search(text, cond)
        self.view = self.__source_layer.run()

    def set_sort(self, sorting: Sequence[str]):
        self.sort_layer.set_sorting(sorting)
        self.view = self.__source_layer.run()

    def get_view_file_size(self):
        return FileSize(sum(video.file_size for video in self.view))

    def get_view_duration(self):
        return Duration(sum(video.raw_microseconds for video in self.view))

    def delete_video(self, index):
        try:
            video = self.view[index]
            self.database.delete_video(video)
            self.__source_layer.delete_video(video)
            self.view = self.__source_layer.run()
            return True
        except OSError:
            return False

    def set_group(self, group_id):
        self.group_layer.set_group_id(group_id)
        self.view = self.__source_layer.run()

    def get_group_field_value(self):
        return self.group_layer.get_field_value()

    def get_sources(self):
        return self.__source_layer.get_sources()

    def get_group_def(self):
        group_def = self.grouping_layer.get_grouping()
        if group_def:
            return {'field': group_def.field,
                    'sorting': group_def.sorting,
                    'reverse': group_def.reverse,
                    'allowSingletons': group_def.allow_singletons,
                    'allowMultiple': group_def.allow_multiple,
                    'group_id': self.group_layer.get_group_id(),
                    'nb_groups': self.classifier_layer.count_groups(),
                    'groups': self.classifier_layer.get_stats(),
                    }
        return None

    def get_search_def(self):
        search_def = self.search_layer.get_search()
        if search_def:
            return {'text': search_def.text, 'cond': search_def.cond}
        return None

    def get_sorting(self):
        return self.sort_layer.get_sorting()

    def count(self):
        return len(self.view)

    def count_total_videos(self):
        return self.__source_layer.count_videos()

    def count_groups(self):
        return self.classifier_layer.count_groups() if self.grouping_layer.get_grouping() else 0

    def get_video(self, index: int) -> Video:
        return self.view[index]

    def load(self):
        self.__source_layer.request_update()
        self.view = self.__source_layer.run()

    def update_view(self):
        self.view = self.__source_layer.run()

    def get_group_id(self):
        return self.group_layer.get_group_id()

    def all_not_found(self):
        return all(NOT_FOUND in source for source in self.__source_layer.get_sources())

    def get_random_found_video(self):
        # type: () -> Video
        # Get all full paths from source definition
        all_paths = []
        for path in self.__source_layer.get_sources():
            desc = TreeUtils.get_source_from_dict(SOURCE_TREE, path)
            if isinstance(desc, dict):
                TreeUtils.collect_full_paths(desc, all_paths, path)
            else:
                all_paths.append(path)
        # Key paths with found videos
        paths = [path for path in all_paths if NOT_FOUND not in path]
        assert paths
        # Iterate as long as we have paths and we have not pick a video
        while paths:
            path_index = random.randrange(len(paths))
            path = paths[path_index]
            del paths[path_index]
            videos = list(TreeUtils.get_source_from_object(self.database, path))
            if videos:
                video_index = random.randrange(len(videos))
                return videos[video_index]
        raise RuntimeError("No videos available.")

    def on_properties_modified(self, properties: Sequence[str]):
        group_def = self.grouping_layer.get_grouping()
        if group_def:
            field = group_def.field[1:] if group_def.field[0] == ':' else group_def.field
            if field in properties:
                self.grouping_layer.request_update()
                self.view = self.__source_layer.run()
                return True

    def get_all_videos(self):
        return self.__source_layer.videos()
