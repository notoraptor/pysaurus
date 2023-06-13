import logging
import random
from abc import abstractmethod
from typing import Any, Dict, List, Sequence, Set

from pysaurus.application import exceptions
from pysaurus.core import functions
from pysaurus.core.profiling import Profiler
from pysaurus.database.viewport.abstract_video_provider import AbstractVideoProvider
from pysaurus.database.viewport.source_def import SourceDef
from pysaurus.database.viewport.view_tools import Group, GroupArray, GroupDef, SearchDef
from pysaurus.video import Video
from pysaurus.video.video_sorting import VideoSorting

logger = logging.getLogger(__name__)
EMPTY_SET = set()


class Layer:
    __slots__ = ("database", "input", "params", "output", "to_update")

    def __init__(self, database):
        from pysaurus.database.database import Database

        self.database: Database = database
        self.input = None
        self.params = self.default_params()
        self.output = None
        self.to_update = False

    def _log(self, *args):
        logger.debug(f"[{type(self).__name__}] {' '.join(str(arg) for arg in args)}")

    def set_input(self, data):
        if self.input is not data:
            self.input = data
            self.to_update = True
            self._log("set_input")

    def set_params(self, **params):
        if self.params != params:
            self.params = params
            self.to_update = True
            self._log("set_params", params)

    def get_output(self):
        if self.to_update:
            with Profiler(f"[{type(self).__name__}] run", self.database.notifier):
                self.run()
            self.to_update = False
            # self._log("run")
        return self.output

    @abstractmethod
    def default_params(self) -> Dict:
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, video_id: int):
        raise NotImplementedError()


class LayerSource(Layer):
    __slots__ = ("source_def", "video_indices_found")
    output: Set[int]

    def __init__(self, database):
        super().__init__(database)
        self.source_def = SourceDef(self.params["sources"])
        self.video_indices_found: List[int] = []

    def set_params(self, *, sources: Sequence[Sequence[str]]):
        if sources is None:
            super().set_params(**self.default_params())
            self.source_def = SourceDef(self.params["sources"])
        else:
            valid_paths = set()
            for path in sources:
                path = tuple(path)
                if path not in valid_paths:
                    assert len(set(path)) == len(path)
                    assert all(flag in Video.FLAGS for flag in path)
                    valid_paths.add(path)
            if valid_paths:
                super().set_params(sources=[list(src) for src in sorted(valid_paths)])
                self.source_def = SourceDef(self.params["sources"])

    @classmethod
    def default_params(cls) -> Dict:
        return {"sources": [["readable"]]}

    def run(self):
        video_indices: Set[int] = set()
        video_indices_found: List[int] = []
        for path in self.params["sources"]:
            source = self.input.search_flags(*path)
            video_indices.update(source)
            if "unreadable" not in path and "not_found" not in path:
                video_indices_found.extend(
                    video_id
                    for video_id in source
                    if self.input.has_video_id(video_id, found=True, readable=True)
                )
        self.output = video_indices
        self.video_indices_found = video_indices_found

    def delete(self, video_id: int):
        self.output.remove(video_id)
        # Video deletion is a rare/not massive operation compared to other.
        # So, we can accept to delete from a list,
        # event if it's not efficient and may be slow.
        # TODO What if deletion becomes massive/frequent?
        # TODO What if videos list is very long ?
        functions.remove_from_list(self.video_indices_found, video_id)

    def get_random_video_id(self) -> int:
        if not self.video_indices_found:
            raise exceptions.NoVideos()
        return random.choice(self.video_indices_found)


class _AbstractLayerGrouping(Layer):
    __slots__ = ("video_id_to_values",)
    output: GroupArray

    def __init__(self, database):
        super().__init__(database)
        self.video_id_to_values: Dict[int, List] = {}

    def _get_grouping_values(self, video_id: int):
        if video_id not in self.video_id_to_values:
            group_def = self.params["grouping"]
            if group_def.is_property:
                values = self._get_prop_values(video_id, group_def.field) or [None]
            else:
                values = [self.database.read_video_field(video_id, group_def.field)]
            self.video_id_to_values[video_id] = values
        return self.video_id_to_values[video_id]

    def _get_prop_values(self, video_id: int, name: str) -> List:
        values = self.database.get_prop_values(video_id, name)
        assert isinstance(values, list)
        if not values and self.database.has_prop_type(name, multiple=False):
            values = [self.database.default_prop_unit(name)]
        return values

    def delete(self, video_id: int):
        groups = []
        group_def = self.params["grouping"]
        if len(self.output) == 1 and self.output[0].field_value is None:
            groups.append(self.output[0])
        else:
            for value in self.video_id_to_values.pop(video_id, ()):
                if self.output.contains_key(value):
                    groups.append(self.output.lookup(value))
        for group in groups:
            if video_id in group.videos:
                group.videos.remove(video_id)
                if not group.videos or (
                    not group_def.allow_singletons and len(group.videos) == 1
                ):
                    group.videos.clear()
                    self.output.remove(group)


class LayerGrouping(_AbstractLayerGrouping):
    __slots__ = ()
    input: Set[int]
    output: GroupArray

    def set_params(self, *, grouping: GroupDef):
        super().set_params(grouping=grouping)

    def default_params(self) -> Dict:
        return {"grouping": GroupDef()}

    def run(self):
        self.video_id_to_values.clear()
        group_def: GroupDef = self.params["grouping"]
        if not group_def:
            groups = [Group(None, self.input)]
        else:
            grouped_videos: Dict[Any, Set[int]] = {}
            with Profiler("Grouping:group videos", self.database.notifier):
                for video_id in self.input:
                    for value in self._get_grouping_values(video_id):
                        grouped_videos.setdefault(value, set()).add(video_id)
            # hack
            if not group_def.is_property and group_def.field == "similarity_id":
                # Remove None (not checked) and -1 (not similar) videos.
                grouped_videos.pop(None, None)
                grouped_videos.pop(-1, None)
            with Profiler("Grouping:get groups", self.database.notifier):
                if group_def.allow_singletons:
                    groups = [Group(f, vs) for f, vs in grouped_videos.items()]
                else:
                    groups = [
                        Group(f, vs) for f, vs in grouped_videos.items() if len(vs) > 1
                    ]
            with Profiler("Grouping:sort groups", self.database.notifier):
                group_def.sort_inplace(groups)
        self.output = GroupArray(group_def.field, group_def.is_property, groups)


class LayerClassifier(_AbstractLayerGrouping):
    __slots__ = ("grouping_layer",)
    input: GroupArray
    output: GroupArray

    def __init__(self, database, grouping_layer: LayerGrouping):
        self.grouping_layer = grouping_layer
        super().__init__(database)

    def _infer_grouping(self):
        return self.grouping_layer.params["grouping"].copy(allow_singletons=True)

    def set_params(self, *, path: List, grouping: GroupDef = None):
        super().set_params(
            path=path, grouping=self._infer_grouping() if grouping is None else grouping
        )

    def default_params(self) -> Dict:
        return {"path": [], "grouping": self._infer_grouping()}

    def run(self):
        self.video_id_to_values.clear()
        data = self.input
        if (
            data.field is None
            or not data.is_property
            or not self.database.has_prop_type(data.field, multiple=True)
            or not self.params["path"]
        ):
            self.output = data
        else:
            path = self.params["path"]
            videos = set.intersection(
                *(set(data.lookup(value).videos) for value in path)
            )
            assert videos, path
            self.output = self._classify_videos(videos, data.field, path)

    def _classify_videos(
        self, videos: Set[int], prop_name: str, path: List
    ) -> GroupArray:
        classes = {}
        for video in videos:
            for value in self._get_grouping_values(video):
                classes.setdefault(value, []).append(video)
        assert None not in classes, classes.keys()
        for value in path:
            classes.pop(value)
        return GroupArray(
            prop_name,
            True,
            self.params["grouping"].sorted(
                [Group(None, videos)]
                + [
                    Group(field_value, group_videos)
                    for field_value, group_videos in classes.items()
                ]
            ),
        )


class LayerGroup(Layer):
    __slots__ = ()
    input: GroupArray
    output: Group

    def set_params(self, *, group_id: int):
        super().set_params(group_id=max(group_id, 0))

    def default_params(self) -> Dict:
        return {"group_id": 0}

    def run(self):
        group_id = min(self.params["group_id"], len(self.input) - 1)
        self.set_params(group_id=group_id)
        self.output = self.input[group_id] if self.input else Group()

    def delete(self, video_id: int):
        if video_id in self.output.videos:
            self.output.videos.remove(video_id)
        if not self.output.videos:
            self.to_update = True


class LayerSearch(Layer):
    __slots__ = ()
    input: Group
    output: Set[int]

    def set_params(self, *, search: SearchDef):
        super().set_params(search=search)

    def default_params(self) -> Dict:
        return {"search": SearchDef()}

    def run(self):
        search_def: SearchDef = self.params["search"]
        if not search_def:
            self.output = self.input.videos
        else:
            self._log("search", search_def)
            self.output = {
                video.video_id
                for video in self.database.search(
                    search_def.text, search_def.cond, self.input.videos
                )
            }

    def delete(self, video_id: int):
        if video_id in self.output:
            self.output.remove(video_id)


class LayerSort(Layer):
    __slots__ = ()
    input: Set[int]
    output: List[int]

    def set_params(self, *, sorting: List[str]):
        super().set_params(
            sorting=list(sorting) if sorting else self.default_params()["sorting"]
        )

    def default_params(self) -> Dict:
        return {"sorting": ["-date"]}

    def run(self):
        sorting = VideoSorting(self.params["sorting"])
        self.output = self.database.sort_video_indices(self.input, sorting)

    def delete(self, video_id: int):
        # See commentary in pysaurus.database.viewport.video_filter.LayerSource.delete
        functions.remove_from_list(self.output, video_id)


class VideoFilter(AbstractVideoProvider):
    __slots__ = ("pipeline", "layers")

    _LAYER_NAMES_ = {
        "source": LayerSource,
        "grouping": LayerGrouping,
        "classifier": LayerClassifier,
        "group": LayerGroup,
        "search": LayerSearch,
        "sort": LayerSort,
    }

    def __init__(self, database):
        super().__init__(database)
        layer_grouping = LayerGrouping(self._database)
        self.pipeline: List[Layer] = [
            LayerSource(self._database),
            layer_grouping,
            LayerClassifier(self._database, grouping_layer=layer_grouping),
            LayerGroup(self._database),
            LayerSearch(self._database),
            LayerSort(self._database),
        ]
        self.layers: Dict[type, Layer] = {type(step): step for step in self.pipeline}
        assert len(self.pipeline) == len(self.layers)

    def set_layer_params(self, layer_cls: type, **params):
        self.layers[layer_cls].set_params(**params)

    def get_layer_params(self, layer_cls, *names):
        params = {name: self.layers[layer_cls].params[name] for name in names}
        return next(iter(params.values())) if len(params) == 1 else params

    def get_view_indices(self) -> Sequence[int]:
        data = self._database
        with Profiler("VideoSelector.get_view", self._database.notifier):
            for layer in self.pipeline:
                layer.set_input(data)
                data = layer.get_output()
            return data

    def delete(self, video):
        for layer in self.pipeline:
            with Profiler(
                f"Deleting video in {type(layer).__name__}", self._database.notifier
            ):
                layer.delete(video.video_id)

    def set_sources(self, paths):
        self.set_layer_params(LayerSource, sources=paths)

    def set_groups(
        self, field, is_property=None, sorting=None, reverse=None, allow_singletons=None
    ):
        self.set_layer_params(
            LayerGrouping,
            grouping=GroupDef(
                field=field,
                is_property=is_property,
                sorting=sorting,
                reverse=reverse,
                allow_singletons=allow_singletons,
            ),
        )
        self.set_layer_params(LayerGroup, group_id=0)
        self.reset_parameters(self.LAYER_CLASSIFIER, self.LAYER_SEARCH)

    def set_classifier_path(self, path):
        self.set_layer_params(LayerClassifier, path=path)

    def set_group(self, group_id):
        self.set_layer_params(LayerGroup, group_id=group_id)

    def set_search(self, text, cond):
        self.set_layer_params(LayerSearch, search=SearchDef(text, cond))

    def set_sort(self, sorting):
        self.set_layer_params(LayerSort, sorting=sorting)

    def get_sources(self):
        return self.get_layer_params(LayerSource, "sources")

    def get_grouping(self):
        return self.get_layer_params(LayerGrouping, "grouping")

    def _convert_field_value_to_group_id(self, field_value):
        layer: LayerGrouping = self.layers[LayerGrouping]
        return layer.output.lookup_index(field_value)

    def get_classifier_path(self):
        return self.get_layer_params(LayerClassifier, "path")

    def _get_classifier_group_value(self, group_id):
        layer: LayerClassifier = self.layers[LayerClassifier]
        return layer.output[group_id].field_value

    def get_group(self):
        return self.get_layer_params(LayerGroup, "group_id")

    def get_search(self):
        return self.get_layer_params(LayerSearch, "search")

    def get_sort(self):
        return self.get_layer_params(LayerSort, "sorting")

    def reset_parameters(self, *layer_names: str):
        for layer_name in layer_names:
            layer_cls = self._LAYER_NAMES_[layer_name]
            self.layers[layer_cls].set_params(**self.layers[layer_cls].default_params())

    def _force_update(self, *layer_names: str):
        for layer_name in layer_names:
            layer_cls = self._LAYER_NAMES_[layer_name]
            self.layers[layer_cls].to_update = True

    def _get_classifier_stats(self):
        layer: LayerClassifier = self.layers[LayerClassifier]
        if layer.output.field and layer.output.is_property:
            converter = functions.identity
        else:
            converter = str
        return [
            {"value": converter(g.field_value), "count": len(g.videos)}
            for g in layer.output
        ]

    def count_source_videos(self):
        layer: LayerSource = self.layers[LayerSource]
        return len(layer.output)

    def get_random_found_video_id(self) -> int:
        layer: LayerSource = self.layers[LayerSource]
        return layer.get_random_video_id()
