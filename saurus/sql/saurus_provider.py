from typing import List, Sequence

from pysaurus.database.viewport.abstract_video_provider import AbstractVideoProvider


class SaurusProvider(AbstractVideoProvider):
    def set_sources(self, paths) -> None:
        pass

    def set_groups(
        self, field, is_property=None, sorting=None, reverse=None, allow_singletons=None
    ) -> None:
        pass

    def set_classifier_path(self, path) -> None:
        pass

    def set_group(self, group_id) -> None:
        pass

    def set_search(self, text, cond) -> None:
        pass

    def set_sort(self, sorting) -> None:
        pass

    def get_sources(self) -> List[List[str]]:
        pass

    def get_grouping(self):
        pass

    def get_classifier_path(self):
        pass

    def get_group(self):
        pass

    def get_search(self):
        pass

    def get_sort(self):
        pass

    def reset_parameters(self, *layer_names: str):
        pass

    def _convert_field_value_to_group_id(self, field_value):
        pass

    def _get_classifier_group_value(self, group_id):
        pass

    def _force_update(self, *layer_names: str):
        pass

    def _get_classifier_stats(self):
        pass

    def count_source_videos(self):
        pass

    def get_view_indices(self) -> Sequence[int]:
        pass

    def delete(self, video_id: int):
        pass
