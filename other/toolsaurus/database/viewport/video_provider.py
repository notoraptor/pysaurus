from typing import Dict, Optional, Sequence

from other.toolsaurus.database.viewport.layers.classifier_layer import ClassifierLayer
from other.toolsaurus.database.viewport.layers.group_layer import GroupLayer
from other.toolsaurus.database.viewport.layers.grouping_layer import GroupingLayer
from other.toolsaurus.database.viewport.layers.layer import Layer
from other.toolsaurus.database.viewport.layers.search_layer import SearchLayer
from other.toolsaurus.database.viewport.layers.sort_layer import SortLayer
from other.toolsaurus.database.viewport.layers.source_layer import SourceLayer
from pysaurus.database.viewport.abstract_video_provider import AbstractVideoProvider
from pysaurus.database.viewport.view_tools import GroupDef
from pysaurus.video import Video


class VideoProvider(AbstractVideoProvider):
    __slots__ = (
        "_database",
        "_source_layer",
        "_grouping_layer",
        "_classifier_layer",
        "_group_layer",
        "_search_layer",
        "_sort_layer",
        "_layer_names",
    )

    def __init__(self, database):
        super().__init__(database)
        self._source_layer = SourceLayer(database)
        self._grouping_layer = GroupingLayer(database)
        self._classifier_layer = ClassifierLayer(database)
        self._group_layer = GroupLayer(database)
        self._search_layer = SearchLayer(database)
        self._sort_layer = SortLayer(database)
        self._layer_names: Dict[str, Layer] = {
            "source": self._source_layer,
            "grouping": self._grouping_layer,
            "classifier": self._classifier_layer,
            "group": self._group_layer,
            "search": self._search_layer,
            "sort": self._sort_layer,
        }

        self._source_layer.set_sub_layer(self._grouping_layer)
        self._grouping_layer.set_sub_layer(self._classifier_layer)
        self._classifier_layer.set_sub_layer(self._group_layer)
        self._group_layer.set_sub_layer(self._search_layer)
        self._search_layer.set_sub_layer(self._sort_layer)

        self._source_layer.set_data(self._database)

    def set_sources(self, paths: Sequence[Sequence[str]]):
        self._source_layer.set_sources(paths)

    def set_groups(
        self, field, is_property=None, sorting=None, reverse=None, allow_singletons=None
    ):
        self._grouping_layer.set_grouping(
            **GroupDef.get_args_from(
                dict(
                    field=field,
                    is_property=is_property,
                    sorting=sorting,
                    reverse=reverse,
                    allow_singletons=allow_singletons,
                )
            )
        )
        self._classifier_layer.reset_parameters()
        self._group_layer.set_group_id(0)
        self._search_layer.reset_parameters()

    def set_classifier_path(self, path: list):
        self._classifier_layer.set_path(path)

    def set_group(self, group_id):
        self._group_layer.set_group_id(group_id)

    def set_search(self, text: Optional[str], cond: Optional[str]):
        self._search_layer.set_search(text, cond)

    def set_sort(self, sorting: Sequence[str]):
        self._sort_layer.set_sorting(sorting)

    def get_sources(self):
        return self._source_layer.get_sources()

    def get_grouping(self):
        return self._grouping_layer.get_grouping()

    def convert_field_value_to_group_id(self, field_value):
        return self._grouping_layer.get_group_id(field_value)

    def get_classifier_path(self):
        return self._classifier_layer.get_path()

    def get_classifier_group_value(self, group_id):
        return self._classifier_layer.get_group_value(group_id)

    def get_group(self):
        return self._group_layer.get_group_id()

    def get_search(self):
        return self._search_layer.get_search()

    def get_sort(self):
        return self._sort_layer.get_sorting()

    def reset_parameters(self, *layer_names: str):
        for layer_name in layer_names:
            self._layer_names[layer_name].reset_parameters()

    def force_update(self, *layer_names: str):
        for layer_name in layer_names:
            self._layer_names[layer_name].request_update()

    def get_classifier_stats(self):
        return self._classifier_layer.get_stats()

    def count_source_videos(self):
        return len(self._source_layer.videos())

    def get_view_indices(self) -> Sequence[int]:
        return [video.video_id for video in self._source_layer.run()]

    def delete(self, video: Video):
        self._source_layer.delete_video(video)
