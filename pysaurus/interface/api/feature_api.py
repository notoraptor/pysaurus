import inspect
import logging
from typing import Any, Callable, Dict, Generator, Optional, Union

from pysaurus.application.application import Application
from pysaurus.application.language.default_language import language_to_dict
from pysaurus.core.classes import StringPrinter
from pysaurus.core.functions import extract_object
from pysaurus.core.notifying import Notification
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase as Db
from pysaurus.database.viewport.abstract_video_provider import (
    AbstractVideoProvider as View,
)

logger = logging.getLogger(__name__)

YieldNotification = Generator[Notification, None, None]


class ProxyFeature:
    __slots__ = ("proxy",)

    def __init__(self, getter: Callable[[], Any], method: Callable, returns=False):
        self.proxy = (getter, method, returns)

    def __call__(self, *args):
        getter, method, returns = self.proxy
        ret = getattr(getter(), method.__name__)(*args)
        return ret if returns else None

    def __str__(self):
        _, method, returns = self.proxy
        return self.signature(method, returns)

    @classmethod
    def signature(cls, method, returns) -> str:
        try:
            ms = inspect.signature(method)
            ret_ann = ms.return_annotation
            ret_accounted = ""
            if ret_ann is ms.empty:
                ret_ann = "undefined"
                if returns:
                    ret_accounted = " (returned)"
            elif not returns and ret_ann is not None:
                ret_accounted = " (ignored)"
            return f"{method.__qualname__} -> {ret_ann}" + ret_accounted
        except Exception as exc:
            raise Exception(method) from exc


class FromDb(ProxyFeature):
    __slots__ = ()

    def __init__(self, api, method, returns=False):
        super().__init__(getter=lambda: api.database, method=method, returns=returns)


class FromView(ProxyFeature):
    __slots__ = ()

    def __init__(self, api, method, returns=False):
        super().__init__(
            getter=lambda: api.database.provider, method=method, returns=returns
        )


class FromApp(ProxyFeature):
    __slots__ = ()

    def __init__(self, api, method, returns=False):
        super().__init__(getter=lambda: api.application, method=method, returns=returns)


class FeatureAPI:
    __slots__ = ("notifier", "application", "database", "_proxies", "_constants")

    def __init__(self, notifier):
        self.notifier = notifier
        self.application = Application(self.notifier)
        self.database: Optional[Db] = None
        self._constants = {
            "PYTHON_DEFAULT_SOURCES": [["readable"]],
            "PYTHON_APP_NAME": self.application.app_name,
            "PYTHON_FEATURE_COMPARISON": True,
            "PYTHON_LANG": language_to_dict(self.application.lang),
            "PYTHON_LANGUAGE": self.application.lang.__language__,
        }
        # We must return value for proxy ending with "!"
        self._proxies: Dict[str, Union[str, ProxyFeature]] = {
            "apply_on_view": FromView(self, View.apply_on_view, True),
            "classifier_back": FromView(self, View.classifier_back),
            "classifier_focus_prop_val": FromView(self, View.classifier_focus_prop_val),
            "classifier_reverse": FromView(self, View.classifier_reverse, True),
            "classifier_select_group": FromView(self, View.classifier_select_group),
            "confirm_unique_moves": FromDb(self, Db.confirm_unique_moves, True),
            "convert_prop_multiplicity": FromDb(self, Db.convert_prop_multiplicity),
            "create_prop_type": FromDb(self, Db.create_prop_type),
            "delete_property_value": FromDb(self, Db.delete_property_value),
            "delete_video": FromDb(self, Db.delete_video),
            "describe_prop_types": FromDb(self, Db.get_prop_types, True),
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
            "set_similarities": FromDb(self, Db.set_similarities),
            "set_sorting": FromView(self, View.set_sort),
            "set_sources": FromView(self, View.set_sources),
            "set_video_folders": FromDb(self, Db.set_folders),
            "set_video_moved": FromDb(self, Db.move_video_entry),
            "set_video_properties": FromDb(self, Db.set_video_properties),
        }

    def __str__(self):
        features = [(name, str(self._proxies[name])) for name in self._proxies] + [
            (name, ProxyFeature.signature(getattr(self, name), True))
            for name in dir(self)
            if "a" <= name[0] <= "z" and inspect.ismethod(getattr(self, name))
        ]
        with StringPrinter() as printer:
            printer.write(f"{type(self).__name__} ({len(features)})")
            for _, feature in sorted(features):
                printer.write(f"\t{feature}")
            return str(printer)

    def __run_feature__(self, name: str, *args) -> Optional:
        with Profiler(f"ApiCall:{name}", self.notifier):
            assert "a" <= name[0] <= "z"
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
                method = getattr(self, name)
                assert inspect.ismethod(method), name
                return method(*args)

    # cannot make proxy
    def get_constants(self) -> Dict[str, Any]:
        return self._constants

    # cannot make proxy ?
    def set_language(self, name) -> Dict[str, str]:
        return language_to_dict(self.application.open_language_from_name(name))

    # cannot make proxy ?
    def backend(self, page_size, page_number, selector=None) -> Dict[str, Any]:
        """Return backend state.

        view: all videos returned by provider
            count
        selection: videos selected in view
            sum of duration
            sum of size
        page: videos displayed in selection
            all video attributes and properties
        """
        context = self.database.provider.get_current_state(
            page_size, page_number, selector
        )
        group_def = self.database.provider.get_group_def()
        videos = context.result_page
        if len(videos) and group_def and group_def["field"] == "similarity_id":
            group_def["common"] = self.database.get_common_fields(
                [video["video_id"] for video in videos]
            )

        return {
            "database": {
                "name": self.database.get_name(),
                "folders": sorted(str(path) for path in self.database.get_folders()),
            },
            "prop_types": self.database.get_prop_types(),
            "videos": context.result_page,
            "pageSize": context.page_size,
            "pageNumber": context.page_number,
            "nbPages": context.nb_pages,
            "nbVideos": context.selection_count,
            "nbViewVideos": context.view_count,
            "nbSourceVideos": self.database.provider.count_source_videos(),
            "validSize": str(context.selection_file_size),
            "validLength": str(context.selection_duration),
            "sources": context.sources,
            "groupDef": group_def,
            "path": context.classifier,
            "searchDef": self.database.provider.get_search_def(),
            "sorting": context.sorting,
        }

    # cannot make proxy ?
    def classifier_concatenate_path(self, to_property) -> None:
        path = self.database.provider.get_classifier_path()
        from_property = self.database.provider.get_grouping().field
        self.database.provider.set_classifier_path([])
        self.database.provider.set_group(0)
        self.database.move_concatenated_prop_val(path, from_property, to_property)
