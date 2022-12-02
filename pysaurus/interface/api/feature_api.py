import sys
from typing import Dict, Optional

from pysaurus.application.application import Application
from pysaurus.core.components import Duration, FileSize
from pysaurus.core.functions import apply_selector, compute_nb_pages, extract_object
from pysaurus.database.database import Database
from pysaurus.database.utils import DEFAULT_SOURCE_DEF
from pysaurus.database.video_features import VideoFeatures
from pysaurus.language.default_language import language_to_dict


class FeatureAPI:
    __slots__ = (
        "notifier",
        "application",
        "database",
        "PYTHON_LANG",
        "PYTHON_LANGUAGE",
        "_proxies",
    )
    PYTHON_DEFAULT_SOURCES = DEFAULT_SOURCE_DEF
    PYTHON_APP_NAME = Application.app_name
    PYTHON_HAS_EMBEDDED_PLAYER = False
    PYTHON_FEATURE_COMPARISON = True

    def __init__(self, notifier):
        self.notifier = notifier
        self.application = Application(self.notifier)
        self.database: Optional[Database] = None
        self.PYTHON_LANG = language_to_dict(self.application.lang)
        self.PYTHON_LANGUAGE = self.application.lang.__language__
        # We must return value for proxy ending with "!"
        self._proxies: Dict[str, str] = {
            "classifier_back": "database.provider.classifier_back",
            "classifier_focus_prop_val": "database.provider.classifier_focus_prop_val",
            "classifier_reverse": "database.provider.classifier_reverse!",
            "classifier_select_group": "database.provider.classifier_select_group",
            "confirm_unique_moves": "database.confirm_unique_moves!",
            "delete_video": "database.delete_video",
            "get_prop_types": "database.describe_prop_types!",
            "prop_to_lowercase": "database.prop_to_lowercase",
            "prop_to_uppercase": "database.prop_to_uppercase",
            "rename_database": "database.rename",
            "set_group": "database.provider.set_group",
            "set_groups": "database.provider.set_groups",
            "set_search": "database.provider.set_search",
            "set_sorting": "database.provider.set_sort",
            "set_sources": "database.provider.set_sources",
            "set_video_moved": "database.move_video_entry",
            "set_video_properties": "database.set_video_properties",
        }

    def __run_feature__(self, name: str, *args):
        assert not name.startswith("_")
        if name in self._proxies:
            path, return_value = self._proxies[name], False
            if path.endswith("!"):
                path = path[:-1]
                return_value = True
            ret = extract_object(self, path)(*args)
            return ret if return_value else None
        else:
            return getattr(self, name)(*args)

    def _parse_video_selector(self, selector: dict, return_videos=False):
        return apply_selector(
            selector, self.database.provider.get_view(), "video_id", return_videos
        )

    # cannot make proxy
    def get_constants(self):
        return {
            key: getattr(self, key) for key in dir(self) if key.startswith("PYTHON_")
        }

    # cannot make proxy
    def get_app_state(self):
        return {
            "languages": [
                {"name": path.title, "path": str(path)}
                for path in self.application.get_language_paths()
            ],
            "databases": [
                {"name": name} for name in self.application.get_database_names()
            ],
        }

    # cannot make proxy ?
    def set_language(self, name):
        return language_to_dict(self.application.open_language_from_name(name))

    # cannot make proxy ?
    def backend(self, callargs, page_size, page_number, selector=None):
        prev_state = self.database.provider.get_unordered_state()

        if callargs:
            ret = self.__run_feature__(callargs[0], *callargs[1:])
            if ret is not None:
                print("Ignored value returned by", callargs, file=sys.stderr)
                print(type(ret), file=sys.stderr)

        # Backend state.
        real_nb_videos = len(self.database.provider.get_view())
        if selector:
            view = self._parse_video_selector(selector, return_videos=True)
        else:
            view = self.database.provider.get_view()
        nb_videos = len(view)
        nb_pages = compute_nb_pages(nb_videos, page_size)
        videos = []
        group_def = self.database.provider.get_group_def()
        if nb_videos:
            page_number = min(max(0, page_number), nb_pages - 1)
            start = page_size * page_number
            end = min(start + page_size, nb_videos)
            videos = [VideoFeatures.to_json(view[index]) for index in range(start, end)]
            if group_def and group_def["field"] == "similarity_id":
                group_def["common"] = VideoFeatures.get_common_fields(view)

        provider_changed = self.database.provider.get_unordered_state() != prev_state

        return {
            "pageSize": page_size,
            "pageNumber": page_number,
            "nbVideos": nb_videos,
            "realNbVideos": real_nb_videos,
            "totalNbVideos": len(self.database.provider.get_all_videos()),
            "nbPages": nb_pages,
            "validSize": str(FileSize(sum(video.file_size for video in view))),
            "validLength": str(
                Duration(
                    sum(video.raw_microseconds for video in view if video.readable)
                )
            ),
            "sources": self.database.provider.get_sources(),
            "groupDef": group_def,
            "searchDef": self.database.provider.get_search_def(),
            "sorting": self.database.provider.get_sort(),
            "videos": videos,
            "path": self.database.provider.get_classifier_path(),
            "prop_types": self.database.describe_prop_types(),
            "database": {
                "name": self.database.name,
                "folders": [str(path) for path in sorted(self.database.video_folders)],
            },
            "viewChanged": provider_changed,
        }

    # cannot make proxy ?
    def classifier_concatenate_path(self, to_property):
        path = self.database.provider.get_classifier_path()
        from_property = self.database.provider.get_grouping().field
        self.database.provider.set_classifier_path([])
        self.database.provider.set_group(0)
        self.database.move_concatenated_prop_val(
            self.database.provider.get_all_videos(), path, from_property, to_property
        )

    # cannot make proxy ?
    def open_random_video(self):
        return str(self.database.provider.choose_random_video().filename.open())

    # cannot make proxy ?
    def playlist(self):
        return str(
            self.database.to_xspf_playlist(self.database.provider.get_view()).open()
        )

    # TODO: abandon
    def open_random_player(self):
        raise NotImplementedError()

    # cannot make proxy ?
    def open_video(self, video_id):
        self.database.get_video_filename(video_id).open()

    # cannot make proxy ?
    def open_containing_folder(self, video_id):
        return str(self.database.get_video_filename(video_id).locate_file())

    # to make proxy
    def count_prop_values(self, name, selector):
        return self.database.count_property_values(
            name, self._parse_video_selector(selector)
        )

    # cannot make proxy ?
    def set_video_folders(self, paths):
        self.database.set_folders(paths)
        self.database.provider.refresh()

    # multicall proxy
    def add_prop_type(self, prop_name: str, prop_type: str, definition, multiple: bool):
        self.database.create_prop_type(prop_name, prop_type, definition, multiple)
        return self.database.describe_prop_types()

    # multicall proxy
    def delete_prop_type(self, name):
        self.database.remove_prop_type(name)
        return self.database.describe_prop_types()

    # multicall proxy
    def rename_property(self, old_name, new_name):
        self.database.rename_prop_type(old_name, new_name)
        return self.database.describe_prop_types()

    # multicall proxy
    def convert_prop_to_unique(self, name):
        self.database.convert_prop_to_unique(name)
        return self.database.describe_prop_types()

    # multicall proxy
    def convert_prop_to_multiple(self, name):
        self.database.convert_prop_to_multiple(name)
        return self.database.describe_prop_types()

    # to make proxy
    def dismiss_similarity(self, video_id):
        self.database.set_similarity(video_id, -1)

    # to make proxy
    def reset_similarity(self, video_id):
        self.database.set_similarity(video_id, None)

    # cannot make proxy ?
    def rename_video(self, video_id, new_title):
        self.database.change_video_file_title(video_id, new_title)
        self.database.provider.refresh()

    # to make proxy ?
    def edit_property_for_videos(self, name, selector, to_add, to_remove):
        self.database.edit_property_for_videos(
            name, self._parse_video_selector(selector), to_add, to_remove
        )

    # to make proxy ?
    def fill_property_with_terms(self, prop_name, only_empty=False):
        self.database.fill_property_with_terms(
            self.database.provider.get_all_videos(), prop_name, only_empty
        )

    # to make proxy ?
    def delete_property_value(self, name, values):
        self.database.delete_property_value(
            self.database.provider.get_all_videos(), name, values
        )

    # to make proxy ?
    def edit_property_value(self, name, old_values, new_value):
        self.database.edit_property_value(
            self.database.provider.get_all_videos(), name, old_values, new_value
        )

    # to make proxy ?
    def move_property_value(self, old_name, values, new_name):
        self.database.move_property_value(
            self.database.provider.get_all_videos(), old_name, values, new_name
        )
