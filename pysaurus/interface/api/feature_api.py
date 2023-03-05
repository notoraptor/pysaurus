import sys
from typing import Any, Callable, Dict, Optional, Union

from pysaurus.application.application import Application
from pysaurus.application.language.default_language import language_to_dict
from pysaurus.core.components import Duration, FileSize
from pysaurus.core.functions import compute_nb_pages, extract_object
from pysaurus.database.database import Database as Db
from pysaurus.database.viewport.abstract_video_provider import (
    AbstractVideoProvider as View,
)
from pysaurus.video.video_features import VideoFeatures


class ProxyFeature:
    def __init__(self, getter: Callable[[], Any], method: Callable, returns=False):
        self.proxy = (getter, method, returns)

    def __call__(self, *args):
        getter, method, returns = self.proxy
        ret = getattr(getter(), method.__name__)(*args)
        return ret if returns else None


class FromDb(ProxyFeature):
    def __init__(self, api, method, returns=False):
        super().__init__(getter=lambda: api.database, method=method, returns=returns)


class FromView(ProxyFeature):
    def __init__(self, api, method, returns=False):
        super().__init__(
            getter=lambda: api.database.provider, method=method, returns=returns
        )


class FromApp(ProxyFeature):
    def __init__(self, api, method, returns=False):
        super().__init__(getter=lambda: api.application, method=method, returns=returns)


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
        self.database: Optional[Db] = None
        self.PYTHON_LANG = language_to_dict(self.application.lang)
        self.PYTHON_LANGUAGE = self.application.lang.__language__
        # We must return value for proxy ending with "!"
        self._proxies: Dict[str, Union[str, ProxyFeature]] = {
            "apply_on_view": FromView(self, View.apply_on_view, True),
            "classifier_back": FromView(self, View.classifier_back),
            "classifier_focus_prop_val": FromView(self, View.classifier_focus_prop_val),
            "classifier_reverse": FromView(self, View.classifier_reverse, True),
            "classifier_select_group": FromView(self, View.classifier_select_group),
            "confirm_unique_moves": FromDb(self, Db.confirm_unique_moves, True),
            "convert_prop_to_multiple": FromDb(self, Db.convert_prop_to_multiple),
            "convert_prop_to_unique": FromDb(self, Db.convert_prop_to_unique),
            "create_prop_type": FromDb(self, Db.create_prop_type),
            "delete_property_value": FromDb(self, Db.delete_property_value),
            "delete_video": FromDb(self, Db.delete_video),
            "describe_prop_types": FromDb(self, Db.describe_prop_types, True),
            "edit_property_value": FromDb(self, Db.edit_property_value),
            "fill_property_with_terms": FromDb(self, Db.fill_property_with_terms),
            "get_database_names": FromApp(self, Application.get_database_names, True),
            "get_language_names": FromApp(self, Application.get_language_names, True),
            "move_property_value": FromDb(self, Db.move_property_value),
            "open_containing_folder": FromDb(self, Db.open_containing_folder, True),
            "open_random_video": FromView(self, View.choose_random_video, True),
            "open_video": FromDb(self, Db.open_video),
            "playlist": FromView(self, View.playlist, True),
            "prop_to_lowercase": FromDb(self, Db.prop_to_lowercase),
            "prop_to_uppercase": FromDb(self, Db.prop_to_uppercase),
            "remove_prop_type": FromDb(self, Db.remove_prop_type),
            "rename_database": FromDb(self, Db.rename),
            "rename_prop_type": FromDb(self, Db.rename_prop_type),
            "rename_video": FromDb(self, Db.change_video_file_title),
            "set_group": FromView(self, View.set_group),
            "set_groups": FromView(self, View.set_groups),
            "set_search": FromView(self, View.set_search),
            "set_similarity": FromDb(self, Db.set_similarity),
            "set_sorting": FromView(self, View.set_sort),
            "set_sources": FromView(self, View.set_sources),
            "set_video_folders": FromDb(self, Db.set_folders),
            "set_video_moved": FromDb(self, Db.move_video_entry),
            "set_video_properties": FromDb(self, Db.set_video_properties),
        }

    def __run_feature__(self, name: str, *args):
        assert not name.startswith("_")
        if name in self._proxies:
            run_def = self._proxies[name]
            if isinstance(run_def, ProxyFeature):
                return run_def(*args)
            else:
                # Keep old resolution code, if any.
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
