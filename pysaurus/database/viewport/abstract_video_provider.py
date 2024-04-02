import random
from abc import ABCMeta, abstractmethod
from typing import List, Optional, Sequence

from pysaurus.application import exceptions
from pysaurus.core import functions
from pysaurus.core.classes import Selector
from pysaurus.video.video_search_context import VideoSearchContext


class AbstractVideoProvider(metaclass=ABCMeta):
    __slots__ = ("_database",)
    LAYER_SOURCE = "source"
    LAYER_GROUPING = "grouping"
    LAYER_CLASSIFIER = "classifier"
    LAYER_GROUP = "group"
    LAYER_SEARCH = "search"
    LAYER_SORT = "sort"
    LAYERS = {
        LAYER_SOURCE,
        LAYER_GROUPING,
        LAYER_CLASSIFIER,
        LAYER_GROUP,
        LAYER_SEARCH,
        LAYER_SORT,
    }

    def __init__(self, database):
        from pysaurus.database.abstract_database import AbstractDatabase

        self._database: AbstractDatabase = database

    @abstractmethod
    def set_sources(self, paths) -> None:
        pass

    @abstractmethod
    def set_groups(
        self, field, is_property=None, sorting=None, reverse=None, allow_singletons=None
    ) -> None:
        pass

    @abstractmethod
    def set_classifier_path(self, path) -> None:
        pass

    @abstractmethod
    def set_group(self, group_id) -> None:
        pass

    @abstractmethod
    def set_search(self, text, cond) -> None:
        pass

    @abstractmethod
    def set_sort(self, sorting) -> None:
        pass

    @abstractmethod
    def get_sources(self) -> List[List[str]]:
        pass

    @abstractmethod
    def get_grouping(self):
        pass

    @abstractmethod
    def get_classifier_path(self):
        pass

    @abstractmethod
    def get_group(self):
        pass

    @abstractmethod
    def get_search(self):
        pass

    @abstractmethod
    def get_sort(self):
        pass

    @abstractmethod
    def reset_parameters(self, *layer_names: str):
        pass

    @abstractmethod
    def _convert_field_value_to_group_id(self, field_value):
        pass

    @abstractmethod
    def _get_classifier_group_value(self, group_id):
        pass

    @abstractmethod
    def _force_update(self, *layer_names: str):
        pass

    @abstractmethod
    def _get_classifier_stats(self):
        pass

    @abstractmethod
    def count_source_videos(self):
        pass

    @abstractmethod
    def get_view_indices(self) -> Sequence[int]:
        pass

    @abstractmethod
    def get_current_state(
        self, page_size: int, page_number: int, selector: Selector = None
    ) -> VideoSearchContext:
        pass

    @abstractmethod
    def delete(self, video_id: int):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()

    def reset(self):
        self.reset_parameters(*self.LAYERS)

    def refresh(self):
        self._force_update(self.LAYER_SOURCE)

    def get_group_def(self):
        group_def = self.get_grouping()
        return (
            group_def.to_dict(
                group_id=self.get_group(), groups=self._get_classifier_stats()
            )
            if group_def
            else None
        )

    def get_search_def(self):
        search_def = self.get_search()
        return search_def.to_dict() if search_def else None

    def get_random_found_video_id(self) -> int:
        video_indices = []
        for path in self.get_sources():
            video_indices.extend(
                video["video_id"]
                for video in self._database.select_videos_fields(
                    ["video_id"], *path, found=True
                )
            )
        if not video_indices:
            raise exceptions.NoVideos()
        return video_indices[random.randrange(len(video_indices))]

    def choose_random_video(self, open_video=True) -> str:
        video_id = self.get_random_found_video_id()
        self.reset_parameters(
            self.LAYER_GROUPING, self.LAYER_CLASSIFIER, self.LAYER_GROUP
        )
        self.set_search(str(video_id), "id")
        if open_video:
            self._database.open_video(video_id)
        return self._database.get_video_filename(video_id).path

    def classifier_select_group(self, group_id: int) -> None:
        path = self.get_classifier_path()
        value = self._get_classifier_group_value(group_id)
        new_path = path + [value]
        self.set_classifier_path(new_path)
        self.set_group(0)

    def classifier_focus_prop_val(self, prop_name, field_value) -> None:
        self.set_groups(
            field=prop_name,
            is_property=True,
            sorting="count",
            reverse=True,
            allow_singletons=True,
        )
        self.reset_parameters(
            self.LAYER_CLASSIFIER, self.LAYER_GROUP, self.LAYER_SEARCH
        )
        self.get_view_indices()
        group_id = self._convert_field_value_to_group_id(field_value)
        self.set_classifier_path([])
        self.get_view_indices()
        # NB: here, classifier and grouping have same group array
        self.classifier_select_group(group_id)

    def classifier_back(self) -> None:
        path = self.get_classifier_path()
        self.set_classifier_path(path[:-1])
        self.set_group(0)

    def classifier_reverse(self) -> List:
        path = list(reversed(self.get_classifier_path()))
        self.set_classifier_path(path)
        return path

    def playlist(self) -> str:
        return str(self._database.to_xspf_playlist(self.get_view_indices()).open())

    def apply_on_view(self, selector, db_fn_name, *db_fn_args) -> Optional:
        callable_methods = {
            "count_property_values": self._database.count_property_values,
            "edit_property_for_videos": self._database.edit_property_for_videos,
        }
        return callable_methods[db_fn_name](
            functions.apply_selector_to_data(selector, self.get_view_indices()),
            *db_fn_args
        )

    def manage_attributes_modified(self, properties: Sequence[str], is_property=True):
        group_def = self.get_grouping()
        if (
            group_def
            and group_def.is_property is is_property
            and group_def.field in properties
        ):
            self._force_update(self.LAYER_GROUPING)
        # If a filename was modified, refresh entire provider.
        if not is_property and "filename" in properties:
            print("A filename was modified, refreshing provider.")
            self.refresh()
