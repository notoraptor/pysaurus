import sys
from typing import Dict, Optional

from pysaurus.application.application import Application
from pysaurus.core.components import Duration, FileSize
from pysaurus.core.functions import compute_nb_pages, extract_object
from pysaurus.database.database import Database
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
    PYTHON_DEFAULT_SOURCES = [("readable",)]
    PYTHON_APP_NAME = Application.app_name
    PYTHON_FEATURE_COMPARISON = True

    def __init__(self, notifier):
        self.notifier = notifier
        self.application = Application(self.notifier)
        self.database: Optional[Database] = None
        self.PYTHON_LANG = language_to_dict(self.application.lang)
        self.PYTHON_LANGUAGE = self.application.lang.__language__
        # We must return value for proxy ending with "!"
        self._proxies: Dict[str, str] = {
            "apply_on_view": "database.provider.apply_on_view!",
            "classifier_back": "database.provider.classifier_back",
            "classifier_focus_prop_val": "database.provider.classifier_focus_prop_val",
            "classifier_reverse": "database.provider.classifier_reverse!",
            "classifier_select_group": "database.provider.classifier_select_group",
            "confirm_unique_moves": "database.confirm_unique_moves!",
            "convert_prop_to_multiple": "database.convert_prop_to_multiple",
            "convert_prop_to_unique": "database.convert_prop_to_unique",
            "create_prop_type": "database.create_prop_type",
            "delete_property_value": "database.delete_property_value",
            "delete_video": "database.delete_video",
            "describe_prop_types": "database.describe_prop_types!",
            "edit_property_value": "database.edit_property_value",
            "fill_property_with_terms": "database.fill_property_with_terms",
            "move_property_value": "database.move_property_value",
            "open_containing_folder": "database.open_containing_folder!",
            "open_random_video": "database.provider.choose_random_video!",
            "open_video": "database.open_video",
            "playlist": "database.provider.playlist!",
            "prop_to_lowercase": "database.prop_to_lowercase",
            "prop_to_uppercase": "database.prop_to_uppercase",
            "remove_prop_type": "database.remove_prop_type",
            "rename_database": "database.rename",
            "rename_prop_type": "database.rename_prop_type",
            "set_group": "database.provider.set_group",
            "set_groups": "database.provider.set_groups",
            "set_search": "database.provider.set_search",
            "set_similarity": "database.set_similarity",
            "set_sorting": "database.provider.set_sort",
            "set_sources": "database.provider.set_sources",
            "set_video_folders": "database.set_folders",
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
            view = self.database.provider.select_from_view(selector, return_videos=True)
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
        self.database.move_concatenated_prop_val(path, from_property, to_property)

    # cannot make proxy ?
    def rename_video(self, video_id, new_title):
        self.database.change_video_file_title(video_id, new_title)
        self.database.provider.refresh()
