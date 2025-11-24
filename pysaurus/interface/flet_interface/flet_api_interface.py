from typing import Collection, Iterable, Sequence

from pysaurus.interface.api.gui_api import GuiAPI


class FletApiInterface:
    __slots__ = ("api",)

    def __init__(self, api: GuiAPI):
        self.api = api

    # Proxies

    def apply_on_view(self, selector, db_fn_name):
        return self.api.__run_feature__("apply_on_view", selector, db_fn_name)

    def classifier_back(self):
        return self.api.__run_feature__("classifier_back")

    def classifier_focus_prop_val(self, prop_name, field_value):
        return self.api.__run_feature__(
            "classifier_focus_prop_val", prop_name, field_value
        )

    def classifier_reverse(self):
        return self.api.__run_feature__("classifier_reverse")

    def classifier_select_group(self, group_id: int):
        return self.api.__run_feature__("classifier_select_group", group_id)

    def confirm_unique_moves(self):
        return self.api.__run_feature__("confirm_unique_moves")

    def convert_prop_multiplicity(self, name: str, multiple: bool):
        return self.api.__run_feature__("convert_prop_multiplicity", name, multiple)

    def create_prop_type(
        self,
        name: str,
        prop_type: str | type,
        definition: bool | int | float | str | Collection,
        multiple: bool,
    ):
        return self.api.__run_feature__(
            "create_prop_type", name, prop_type, definition, multiple
        )

    def delete_property_values(self, name: str, values: list):
        return self.api.__run_feature__("delete_property_values", name, values)

    def delete_video(self, video_id: int):
        return self.api.__run_feature__("delete_video", video_id)

    def describe_prop_types(
        self, name=None, with_type=None, multiple=None, with_enum=None, default=None
    ):
        return self.api.__run_feature__(
            "describe_prop_types", name, with_type, multiple, with_enum, default
        )

    def replace_property_values(self, name: str, old_values: list, new_value: object):
        return self.api.__run_feature__(
            "replace_property_values", name, old_values, new_value
        )

    def fill_property_with_terms(self, prop_name: str, only_empty=False):
        return self.api.__run_feature__(
            "fill_property_with_terms", prop_name, only_empty
        )

    def get_database_names(self):
        return self.api.__run_feature__("get_database_names")

    def get_language_names(self):
        return self.api.__run_feature__("get_language_names")

    def move_property_values(self, values: list, old_name: str, new_name: str):
        return self.api.__run_feature__(
            "move_property_values", values, old_name, new_name
        )

    def open_containing_folder(self, video_id: int):
        return self.api.__run_feature__("open_containing_folder", video_id)

    def open_random_video(self, open_video=True):
        return self.api.__run_feature__("open_random_video", open_video)

    def open_video(self, video_id):
        return self.api.__run_feature__("open_video", video_id)

    def playlist(self):
        return self.api.__run_feature__("playlist")

    def apply_on_prop_value(self, prop_name, edition):
        return self.api.__run_feature__("apply_on_prop_value", prop_name, edition)

    def remove_prop_type(self, name):
        return self.api.__run_feature__("remove_prop_type", name)

    def rename_database(self, new_name: str):
        return self.api.__run_feature__("rename_database", new_name)

    def rename_prop_type(self, old_name, new_name):
        return self.api.__run_feature__("rename_prop_type", old_name, new_name)

    def rename_video(self, video_id: int, new_title: str):
        return self.api.__run_feature__("rename_video", video_id, new_title)

    def set_group(self, group_id):
        return self.api.__run_feature__("set_group", group_id)

    def set_groups(
        self, field, is_property=None, sorting=None, reverse=None, allow_singletons=None
    ):
        return self.api.__run_feature__(
            "set_groups", field, is_property, sorting, reverse, allow_singletons
        )

    def set_search(self, text, cond):
        return self.api.__run_feature__("set_search", text, cond)

    def set_similarities(self, indices: Iterable[int], values: Iterable[int | None]):
        return self.api.__run_feature__("set_similarities", indices, values)

    def set_sorting(self, sorting):
        return self.api.__run_feature__("set_sorting", sorting)

    def set_sources(self, paths):
        return self.api.__run_feature__("set_sources", paths)

    def set_video_folders(self, folders):
        return self.api.__run_feature__("set_video_folders", folders)

    def set_video_moved(self, from_id, to_id):
        return self.api.__run_feature__("set_video_moved", from_id, to_id)

    def set_video_properties(self, video_id: int, properties: dict, merge=False):
        return self.api.__run_feature__(
            "set_video_properties", video_id, properties, merge
        )

    def clipboard(self, text: str):
        return self.api.__run_feature__("clipboard", text)

    def select_directory(self, default=None):
        return self.api.__run_feature__("select_directory", default)

    def select_file(self):
        return self.api.__run_feature__("select_file")

    # Methods

    def backend(self, page_size, page_number, selector=None):
        return self.api.__run_feature__("backend", page_size, page_number, selector)

    def cancel_copy(self):
        return self.api.__run_feature__("cancel_copy")

    def classifier_concatenate_path(self, to_property):
        return self.api.__run_feature__("classifier_concatenate_path", to_property)

    def close_app(self):
        return self.api.__run_feature__("close_app")

    def close_database(self):
        return self.api.__run_feature__("close_database")

    def create_database(self, name: str, folders: Sequence[str], update: bool):
        return self.api.__run_feature__("create_database", name, folders, update)

    def delete_database(self):
        return self.api.__run_feature__("delete_database")

    def find_similar_videos(self):
        return self.api.__run_feature__("find_similar_videos")

    def get_constants(self):
        return self.api.__run_feature__("get_constants")

    def move_video_file(self, video_id: int, directory: str):
        return self.api.__run_feature__("move_video_file", video_id, directory)

    def open_database(self, name: str, update: bool):
        return self.api.__run_feature__("open_database", name, update)

    def open_from_server(self, video_id):
        return self.api.__run_feature__("open_from_server", video_id)

    def set_language(self, name):
        return self.api.__run_feature__("set_language", name)

    def update_database(self):
        return self.api.__run_feature__("update_database")
