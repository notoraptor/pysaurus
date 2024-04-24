from typing import *
from abc import abstractmethod
from pysaurus.core.notifications import Notification
from pysaurus.interface.api.gui_api import GuiAPI


class FletApiWrapper(GuiAPI):
    @abstractmethod
    def _notify(self, notification: Notification) -> None:
        raise NotImplementedError()

    def apply_on_view(self, selector, db_fn_name):
        return self._proxies["apply_on_view"](selector, db_fn_name)

    def classifier_back(self):
        return self._proxies["classifier_back"]()

    def classifier_focus_prop_val(self, prop_name, field_value):
        return self._proxies["classifier_focus_prop_val"](prop_name, field_value)

    def classifier_reverse(self):
        return self._proxies["classifier_reverse"]()

    def classifier_select_group(self, group_id: int):
        return self._proxies["classifier_select_group"](group_id)

    def confirm_unique_moves(self):
        return self._proxies["confirm_unique_moves"]()

    def convert_prop_multiplicity(self, name: str, multiple: bool):
        return self._proxies["convert_prop_multiplicity"](name, multiple)

    def create_prop_type(
        self,
        name: str,
        prop_type: Union[str, type],
        definition: Union[bool, int, float, str, Collection],
        multiple: bool,
    ):
        return self._proxies["create_prop_type"](name, prop_type, definition, multiple)

    def delete_property_value(self, name: str, values: list):
        return self._proxies["delete_property_value"](name, values)

    def delete_video(self, video_id: int):
        return self._proxies["delete_video"](video_id)

    def describe_prop_types(
        self, name=None, with_type=None, multiple=None, with_enum=None, default=None
    ):
        return self._proxies["describe_prop_types"](
            name, with_type, multiple, with_enum, default
        )

    def edit_property_value(self, name: str, old_values: list, new_value: object):
        return self._proxies["edit_property_value"](name, old_values, new_value)

    def fill_property_with_terms(self, prop_name: str, only_empty=False):
        return self._proxies["fill_property_with_terms"](prop_name, only_empty)

    def get_database_names(self):
        return self._proxies["get_database_names"]()

    def get_language_names(self):
        return self._proxies["get_language_names"]()

    def move_property_value(self, old_name: str, values: list, new_name: str):
        return self._proxies["move_property_value"](old_name, values, new_name)

    def open_containing_folder(self, video_id: int):
        return self._proxies["open_containing_folder"](video_id)

    def open_random_video(self, open_video=True):
        return self._proxies["open_random_video"](open_video)

    def open_video(self, video_id):
        return self._proxies["open_video"](video_id)

    def playlist(self):
        return self._proxies["playlist"]()

    def prop_to_lowercase(self, prop_name):
        return self._proxies["prop_to_lowercase"](prop_name)

    def prop_to_uppercase(self, prop_name):
        return self._proxies["prop_to_uppercase"](prop_name)

    def remove_prop_type(self, name):
        return self._proxies["remove_prop_type"](name)

    def rename_database(self, new_name: str):
        return self._proxies["rename_database"](new_name)

    def rename_prop_type(self, old_name, new_name):
        return self._proxies["rename_prop_type"](old_name, new_name)

    def rename_video(self, video_id: int, new_title: str):
        return self._proxies["rename_video"](video_id, new_title)

    def set_group(self, group_id):
        return self._proxies["set_group"](group_id)

    def set_groups(
        self, field, is_property=None, sorting=None, reverse=None, allow_singletons=None
    ):
        return self._proxies["set_groups"](
            field, is_property, sorting, reverse, allow_singletons
        )

    def set_search(self, text, cond):
        return self._proxies["set_search"](text, cond)

    def set_similarities(self, indices: Iterable[int], values: Iterable[Optional[int]]):
        return self._proxies["set_similarities"](indices, values)

    def set_sorting(self, sorting):
        return self._proxies["set_sorting"](sorting)

    def set_sources(self, paths):
        return self._proxies["set_sources"](paths)

    def set_video_folders(self, folders):
        return self._proxies["set_video_folders"](folders)

    def set_video_moved(self, from_id, to_id):
        return self._proxies["set_video_moved"](from_id, to_id)

    def set_video_properties(self, video_id: int, properties: dict, merge=False):
        return self._proxies["set_video_properties"](video_id, properties, merge)

    def clipboard(self, text: str):
        return self._proxies["clipboard"](text)

    def select_directory(self, default=None):
        return self._proxies["select_directory"](default)

    def select_file(self):
        return self._proxies["select_file"]()
