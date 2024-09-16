import inspect
import operator
from typing import Any, Dict, Optional, Union

from pysaurus.application.application import Application
from pysaurus.application.language.default_language import language_to_dict
from pysaurus.core.classes import Selector, StringPrinter
from pysaurus.core.constants import PYTHON_DEFAULT_SOURCES
from pysaurus.core.file_utils import create_xspf_playlist
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase as Db
from pysaurus.interface.api.api_utils.proxy_feature import (
    FromApp,
    FromDb,
    FromView,
    ProxyFeature,
)
from pysaurus.video.video_constants import COMMON_FIELDS
from pysaurus.video.video_features import VideoFeatures
from pysaurus.video_provider.abstract_video_provider import (
    AbstractVideoProvider as View,
)


class FeatureAPI:
    __slots__ = ("notifier", "application", "database", "_proxies", "_constants")

    def __init__(self, notifier):
        self.notifier = notifier
        self.application = Application(self.notifier)
        self.database: Optional[Db] = None
        self._constants = {
            "PYTHON_DEFAULT_SOURCES": PYTHON_DEFAULT_SOURCES,
            "PYTHON_APP_NAME": self.application.app_name,
            "PYTHON_FEATURE_COMPARISON": True,
            "PYTHON_LANG": language_to_dict(self.application.lang),
            "PYTHON_LANGUAGE": self.application.lang.__language__,
        }
        # We must return value for proxy ending with "!"
        self._proxies: Dict[str, Union[str, ProxyFeature]] = {
            "apply_on_view": FromView(self, View.apply_on_view, True),
            "apply_on_prop_value": FromDb(self, Db.apply_on_prop_value),
            "classifier_back": FromView(self, View.classifier_back),
            "classifier_focus_prop_val": FromView(self, View.classifier_focus_prop_val),
            "classifier_reverse": FromView(self, View.classifier_reverse, True),
            "classifier_select_group": FromView(self, View.classifier_select_group),
            "confirm_unique_moves": FromDb(self, Db.confirm_unique_moves, True),
            "convert_prop_multiplicity": FromDb(self, Db.convert_prop_multiplicity),
            "create_prop_type": FromDb(self, Db.create_prop_type),
            "delete_property_values": FromDb(self, Db.delete_property_values),
            "delete_video": FromDb(self, Db.delete_video),
            "describe_prop_types": FromDb(self, Db.get_prop_types, True),
            "replace_property_values": FromDb(self, Db.replace_property_values),
            "fill_property_with_terms": FromDb(self, Db.fill_property_with_terms),
            "get_database_names": FromApp(self, Application.get_database_names, True),
            "get_language_names": FromApp(self, Application.get_language_names, True),
            "move_property_values": FromDb(self, Db.move_property_values),
            "open_random_video": FromView(self, View.choose_random_video, True),
            "open_video": FromDb(self, Db.open_video),
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
            (name, ProxyFeature.info_signature(getattr(self, name), True))
            for name in dir(self)
            if "a" <= name[0] <= "z" and inspect.ismethod(getattr(self, name))
        ]
        with StringPrinter() as printer:
            printer.write(f"{type(self).__name__} ({len(features)})")
            for _, feature in sorted(features):
                printer.write(f"\t{feature}")
            return str(printer)

    def __run_feature__(self, name: str, *args) -> Optional:
        assert "a" <= name[0] <= "z"
        with Profiler(f"ApiCall:{name}", self.notifier):
            if name in self._proxies:
                return self._proxies[name](*args)
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
        """Return backend state."""
        if selector is not None and isinstance(selector, dict):
            selector = Selector.parse_dict(selector)
        context = self.database.provider.get_current_state(
            page_size, page_number, selector
        )
        group_def = self.database.provider.get_group_def()
        videos = context.result_page
        if len(videos) and group_def and group_def["field"] == "similarity_id":
            group_def["common"] = VideoFeatures.get_common_fields(
                videos, getfield=operator.getitem, fields=COMMON_FIELDS
            )

        return {
            "database": {
                "name": self.database.get_name(),
                "folders": sorted(str(path) for path in self.database.get_folders()),
            },
            "prop_types": self.database.get_prop_types(),
            "nbSourceVideos": self.database.provider.count_source_videos(),
            "groupDef": group_def,
            **context.json(),
        }

    # cannot make proxy ?
    def classifier_concatenate_path(self, to_property) -> None:
        path = self.database.provider.get_classifier_path()
        from_property = self.database.provider.get_grouping().field
        self.database.provider.set_classifier_path([])
        self.database.provider.set_group(0)
        self.database.move_concatenated_prop_val(path, from_property, to_property)

    def playlist(self) -> str:
        db = self.database
        pv = db.provider
        return str(
            create_xspf_playlist(
                map(db.get_video_filename, pv.get_view_indices())
            ).open()
        )

    def open_containing_folder(self, video_id: int) -> str:
        return str(self.database.get_video_filename(video_id).locate_file())
