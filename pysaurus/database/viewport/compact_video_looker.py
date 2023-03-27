from typing import Any, Dict, List, Sequence

from pysaurus.core import functions
from pysaurus.core.profiling import Profiler
from pysaurus.database.viewport.abstract_video_provider import AbstractVideoProvider
from pysaurus.database.viewport.source_def import SourceDef
from pysaurus.database.viewport.view_tools import Group, GroupDef, SearchDef
from pysaurus.video import Video
from pysaurus.video.video_sorting import VideoSorting


class CompactVideoLooker(AbstractVideoProvider):
    __slots__ = (
        "source_def",
        "group_def",
        "classifier_path",
        "group_id",
        "search_def",
        "sort_def",
        "_filter_changed",
        "_sort_changed",
        "_classifier_stats",
        "_nb_source_videos",
        "_video_indices",
    )
    DEFAULT_SOURCES = [("readable",)]
    DEFAULT_SORTING = ["-date"]

    def __init__(self, database):
        super().__init__(database)
        # Parameters
        self.source_def = SourceDef(self.DEFAULT_SOURCES)
        self.group_def = GroupDef()
        self.classifier_path = []
        self.group_id = 0
        self.search_def = SearchDef()
        self.sort_def = VideoSorting(self.DEFAULT_SORTING)
        # Update flags
        self._filter_changed = True
        self._sort_changed = True
        # Cache
        self._nb_source_videos = 0
        self._classifier_stats: List[Group] = []
        self._video_indices: List[int] = []

    @property
    def notifier(self):
        return self._database.notifier

    def set_sources(self, paths: Sequence[Sequence[str]]):
        new_source_def = SourceDef(paths) if paths else SourceDef(self.DEFAULT_SOURCES)
        if self.source_def != new_source_def:
            self.source_def = new_source_def
            self._filter_changed = True

    def set_groups(
        self, field, is_property=None, sorting=None, reverse=None, allow_singletons=None
    ):
        new_group_def = GroupDef(field, is_property, sorting, reverse, allow_singletons)
        if self.group_def != new_group_def:
            self.group_def = new_group_def
            self._filter_changed = True
            self.reset_parameters(
                self.LAYER_CLASSIFIER, self.LAYER_GROUP, self.LAYER_SEARCH
            )

    def set_classifier_path(self, path: Sequence[str]):
        if self.classifier_path != path:
            self.classifier_path = path
            self._filter_changed = True
            self.reset_parameters(self.LAYER_GROUP, self.LAYER_SEARCH)

    def set_group(self, group_id):
        if self.group_id != group_id:
            self.group_id = group_id
            self._filter_changed = True

    def set_search(self, text, cond):
        new_search_def = SearchDef(text, cond)
        if self.search_def != new_search_def:
            self.search_def = new_search_def
            self._filter_changed = True

    def set_sort(self, sorting: Sequence[str]):
        new_sort_def = VideoSorting(sorting or self.DEFAULT_SORTING)
        if self.sort_def != new_sort_def:
            self.sort_def = new_sort_def
            self._sort_changed = True

    def get_sources(self):
        return sorted(self.source_def.sources)

    def get_grouping(self):
        return self.group_def

    def get_classifier_path(self):
        return self.classifier_path

    def get_group(self):
        return self.group_id

    def get_search(self):
        return self.search_def

    def get_sort(self) -> Sequence[str]:
        return self.sort_def.to_string_list()

    def reset_parameters(self, *layer_names: str):
        layer_names = set(layer_names)
        if self.LAYER_SOURCE in layer_names:
            self.set_sources(self.DEFAULT_SOURCES)
        if self.LAYER_GROUPING in layer_names:
            self.set_groups(None)
        if self.LAYER_CLASSIFIER in layer_names:
            self.set_classifier_path([])
        if self.LAYER_GROUP in layer_names:
            self.set_group(0)
        if self.LAYER_SEARCH in layer_names:
            self.set_search(None, None)
        if self.LAYER_SORT in layer_names:
            self.set_sort(self.DEFAULT_SORTING)

    def _convert_field_value_to_group_id(self, field_value):
        for group_id, group in enumerate(self._classifier_stats):
            if group.field == field_value:
                return group_id
        raise ValueError(f"Cannot convert value to group ID: {field_value}")

    def _get_classifier_group_value(self, group_id):
        return self._classifier_stats[group_id].field

    def _force_update(self, *layer_names: str):
        layer_names = set(layer_names)
        if self.LAYER_SORT in layer_names:
            self._sort_changed = True
            layer_names.remove(self.LAYER_SORT)
        if layer_names:
            self._filter_changed = True

    def _get_classifier_stats(self):
        assert not self._filter_changed
        if self.group_def and self.group_def.is_property:
            converter = functions.identity
        else:
            converter = str
        return [
            {"value": converter(g.field_value), "count": g.count}
            for g in self._classifier_stats
        ]

    def count_source_videos(self) -> int:
        assert not self._filter_changed
        return self._nb_source_videos

    def delete(self, video):
        self._filter_changed = True

    @Profiler.profile_method()
    def get_view_indices(self) -> Sequence[int]:
        db = self._database
        if self._filter_changed:
            self._sort_changed = True

            # 1. source
            videos = [
                video for video in db.query() if self.source_def.contains_video(video)
            ]
            self._nb_source_videos = len(videos)

            # 5. search
            if self.search_def:
                videos = list(
                    db.search(self.search_def.text, self.search_def.cond, videos)
                )

            # 2. grouping
            self._classifier_stats = []
            if self.group_def:
                g_field = self.group_def.field
                # 3. classifier
                classifier_stats: Dict[Any, List[Video]] = {}
                if self.classifier_path:
                    assert self.group_def.is_property
                    classifier_set = set(self.classifier_path)
                    for video in videos:
                        property_values = set(
                            db.get_prop_values(video.video_id, g_field, True)
                        )
                        if classifier_set.issubset(property_values):
                            for value in property_values - classifier_set:
                                classifier_stats.setdefault(value, []).append(video)
                            classifier_stats.setdefault(None, []).append(video)
                elif self.group_def.is_property:
                    for video in videos:
                        for value in db.get_prop_values(
                            video.video_id, g_field, True
                        ) or [None]:
                            classifier_stats.setdefault(value, []).append(video)
                else:
                    for video in videos:
                        classifier_stats.setdefault(getattr(video, g_field), []).append(
                            video
                        )
                self._classifier_stats = self.group_def.sort(
                    Group(field, group_videos)
                    for field, group_videos in classifier_stats.items()
                    if self.group_def.allow_singletons or len(group_videos) > 1
                )
                # 4. group
                videos = self._classifier_stats[self.group_id].videos

            self._video_indices = [video.video_id for video in videos]
            self._filter_changed = False

        if self._sort_changed:
            self._video_indices = db.sort_video_indices(
                self._video_indices, self.sort_def
            )
            self._sort_changed = False

        return self._video_indices
