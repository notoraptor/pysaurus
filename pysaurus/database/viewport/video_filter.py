from abc import abstractmethod
from typing import Dict, List, Sequence, Set

from pysaurus.core import functions
from pysaurus.database.video import Video
from pysaurus.database.video_sorting import VideoSorting
from pysaurus.database.viewport.abstract_video_provider import AbstractVideoProvider
from pysaurus.database.viewport.view_tools import (
    Group,
    GroupArray,
    GroupDef,
    SearchDef,
    VideoArray,
)


class Layer:
    __slots__ = ("database", "input", "params", "output", "to_update")

    def __init__(self, database):
        from pysaurus.database.database import Database

        self.database: Database = database
        self.input = None
        self.params = self.default_params()
        self.output = None
        self.to_update = False

    def __log(self, *args, **kwargs):
        print(f"[{type(self).__name__}]", *args, **kwargs)

    def set_input(self, data):
        if self.input is not data:
            self.input = data
            self.to_update = True
            self.__log("set_input")

    def set_params(self, **params):
        if self.params != params:
            self.params = params
            self.to_update = True
            self.__log("set_params", params)

    def get_output(self):
        if self.to_update:
            self.run()
            self.to_update = False
            self.__log("run")
        return self.output

    @abstractmethod
    def default_params(self) -> Dict:
        raise NotImplementedError()

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, video: Video):
        raise NotImplementedError()


class LayerSource(Layer):
    __slots__ = ()
    output: Set[Video]

    def set_params(self, *, sources: Sequence[Sequence[str]]):
        if sources is None:
            super().set_params(**self.default_params())
        else:
            valid_paths = set()
            for path in sources:
                path = tuple(path)
                if path not in valid_paths:
                    assert len(set(path)) == len(path)
                    assert all(Video.is_flag(flag) for flag in path)
                    valid_paths.add(path)
            if valid_paths:
                super().set_params(sources=sorted(valid_paths))

    @classmethod
    def default_params(cls) -> Dict:
        return {"sources": [("readable",)]}

    def run(self):
        source = []
        for path in self.params["sources"]:
            source.extend(self.input.get_videos(*path))
        unique_videos = set(source)
        assert len(unique_videos) == len(source), (len(unique_videos), len(source))
        self.output: Set[Video] = unique_videos

    def delete(self, video: Video):
        self.output.remove(video)


class _AbstractLayerGrouping(Layer):
    __slots__ = ()
    output: GroupArray

    def _get_grouping_values(self, video, group_def: GroupDef):
        if group_def.is_property:
            return self.database.get_prop_values(
                video, group_def.field, default=True
            ) or [None]
        else:
            return [getattr(video, group_def.field)]

    def delete(self, video):
        groups = []
        group_def = self.params["grouping"]
        if len(self.output) == 1 and self.output[0].field_value is None:
            groups.append(self.output[0])
        else:
            for value in self._get_grouping_values(video, group_def):
                if self.output.contains_key(value):
                    groups.append(self.output.lookup(value))
        for group in groups:
            if video in group.videos:
                group.videos.remove(video)
                if not group.videos or (
                    not group_def.allow_singletons and len(group.videos) == 1
                ):
                    group.videos.clear()
                    self.output.remove(group)


class LayerGrouping(_AbstractLayerGrouping):
    __slots__ = ()
    input: Set[Video]
    output: GroupArray

    def set_params(self, *, grouping: GroupDef):
        super().set_params(grouping=grouping)

    def default_params(self) -> Dict:
        return {"grouping": GroupDef()}

    def run(self):
        group_def: GroupDef = self.params["grouping"]
        if not group_def:
            groups = [Group(None, list(self.input))]
        else:
            grouped_videos = {}
            for video in self.input:
                for value in self._get_grouping_values(video, group_def):
                    grouped_videos.setdefault(value, []).append(video)
            # hack
            if not group_def.is_property and group_def.field == "similarity_id":
                # Remove None (not checked) and -1 (not similar) videos.
                grouped_videos.pop(None, None)
                grouped_videos.pop(-1, None)
            groups = group_def.sort(
                Group(field_value, videos)
                for field_value, videos in grouped_videos.items()
                if group_def.allow_singletons or len(videos) > 1
            )
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

    def set_params(self, *, path: List, grouping: GroupDef):
        super().set_params(
            path=path, grouping=self._infer_grouping() if grouping is None else grouping
        )

    def default_params(self) -> Dict:
        return {"path": [], "grouping": self._infer_grouping()}

    def run(self):
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
        self, videos: Set[Video], prop_name: str, path: List
    ) -> GroupArray:
        classes = {}
        for video in videos:
            for value in video.properties.get(prop_name, []):
                classes.setdefault(value, []).append(video)
        for value in path:
            classes.pop(value)
        return GroupArray(
            prop_name,
            True,
            self.params["grouping"].sort(
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

    def delete(self, video):
        if video in self.output.videos:
            self.output.videos.remove(video)
        if not self.output.videos:
            self.to_update = True


class LayerSearch(Layer):
    __slots__ = ()
    input: Group
    output: VideoArray

    def set_params(self, *, search: SearchDef):
        super().set_params(search=search)

    def default_params(self) -> Dict:
        return {"search": SearchDef()}

    def run(self):
        # TODO Move search logic as a method to (Json)Database, next to method query()?
        search_def: SearchDef = self.params["search"]
        if not search_def:
            self.output = self.input.videos
        else:
            data = self.input
            term_to_videos = self.database.indexer.get_index()
            terms = functions.string_to_pieces(search_def.text)
            if search_def.cond == "exact":
                selection_and = set.intersection(
                    set(data.videos),
                    *(
                        [
                            term_to_videos[term]
                            for term in terms
                            if term in term_to_videos
                        ]
                        or [set()]
                    ),
                )
                selection = (
                    video
                    for video in selection_and
                    if self.database.indexer.video_has_terms_exact(video, terms)
                )
            elif search_def.cond == "and":
                selection = set.intersection(
                    set(data.videos),
                    *(
                        [
                            term_to_videos[term]
                            for term in terms
                            if term in term_to_videos
                        ]
                        or [set()]
                    ),
                )
            elif search_def.cond == "id":
                (term,) = terms
                video_id = int(term)
                # TODO Database.id_to_video used here
                selection = (
                    [self.database.id_to_video[video_id]]
                    if video_id in self.database.id_to_video
                    else []
                )
            else:
                assert search_def.cond == "or"
                selection = set(data.videos) & set.union(
                    *(
                        [
                            term_to_videos[term]
                            for term in terms
                            if term in term_to_videos
                        ]
                        or [set()]
                    )
                )
            self.output = VideoArray(selection)

    def delete(self, video):
        if video in self.output:
            self.output.remove(video)


class LayerSort(Layer):
    __slots__ = ()
    input: VideoArray
    output: VideoArray

    def set_params(self, *, sorting: List[str]):
        super().set_params(
            sorting=list(sorting) if sorting else self.default_params()["sorting"]
        )

    def default_params(self) -> Dict:
        return {"sorting": ["-date"]}

    def run(self):
        sorting = VideoSorting(self.params["sorting"])
        self.output = VideoArray(
            sorted(self.input, key=lambda video: video.to_comparable(sorting))
        )

    def delete(self, video):
        if video in self.output:
            self.output.remove(video)


_LAYER_NAMES_ = {
    "source": LayerSource,
    "grouping": LayerGrouping,
    "classifier": LayerClassifier,
    "group": LayerGroup,
    "search": LayerSearch,
    "sort": LayerSort,
}


class VideoSelector(AbstractVideoProvider):
    __slots__ = ("_database", "pipeline", "layers")

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

    def get_view(self):
        data = self._database
        for layer in self.pipeline:
            layer.set_input(data)
            data = layer.get_output()
        print("----- selected -----")
        return data

    def delete(self, video):
        for layer in self.pipeline:
            layer.delete(video)

    def set_sources(self, paths):
        self.set_layer_params(LayerSource, sources=paths)

    def set_groups(self, **group_def_args):
        self.set_layer_params(LayerGrouping, grouping=GroupDef(**group_def_args))
        self.set_layer_params(LayerGroup, group_id=0)
        self.reset_parameters("classifier", "search")

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

    def convert_field_value_to_group_id(self, field_value):
        layer: LayerGrouping = self.layers[LayerGrouping]
        return layer.output.lookup_index(field_value)

    def get_classifier_path(self):
        return self.get_layer_params(LayerClassifier, "path")

    def get_classifier_group_value(self, group_id):
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
            layer_cls = _LAYER_NAMES_[layer_name]
            self.layers[layer_cls].set_params(**self.layers[layer_cls].default_params())

    def force_update(self, *layer_names: str):
        for layer_name in layer_names:
            layer_cls = _LAYER_NAMES_[layer_name]
            self.layers[layer_cls].to_update = True

    def get_classifier_stats(self):
        layer: LayerClassifier = self.layers[LayerClassifier]
        if layer.output.field and layer.output.is_property:
            converter = functions.identity
        else:
            converter = str
        return [
            {"value": converter(g.field_value), "count": len(g.videos)}
            for g in layer.output
        ]

    def get_all_videos(self):
        layer: LayerSource = self.layers[LayerSource]
        return layer.output
