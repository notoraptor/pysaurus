import inspect
from typing import Any, Optional

from pysaurus.application.application import Application
from pysaurus.application.language.default_language import language_to_dict
from pysaurus.core.classes import Selector, StringPrinter
from pysaurus.core.constants import PYTHON_DEFAULT_SOURCES
from pysaurus.core.file_utils import create_xspf_playlist
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase as Db
from pysaurus.database.database_algorithms import DatabaseAlgorithms as Algo
from pysaurus.database.database_operations import DatabaseOperations as Ops
from pysaurus.interface.api.api_utils.proxy_feature import (
    FromAlgo,
    FromApp,
    FromDb,
    FromOps,
    FromView,
    ProxyFeature,
)
from pysaurus.video.database_context import DatabaseContext
from pysaurus.video_provider.abstract_video_provider import (
    AbstractVideoProvider as View,
)


class FeatureAPI:
    __slots__ = ("notifier", "application", "database", "_proxies", "_constants")

    def __init__(self, notifier):
        self.notifier = notifier
        self.application = Application(self.notifier)
        self.database: Db | None = None
        self._constants = {
            "PYTHON_DEFAULT_SOURCES": PYTHON_DEFAULT_SOURCES,
            "PYTHON_APP_NAME": self.application.app_name,
            "PYTHON_FEATURE_COMPARISON": True,
            "PYTHON_LANG": "english",
            "PYTHON_LANGUAGE": "english",
        }
        # We must return value for proxy ending with "!"
        self._proxies: dict[str, str | ProxyFeature] = {
            "apply_on_view": FromView(self, View.apply_on_view, True),
            "apply_on_prop_value": FromOps(self, Ops.apply_on_prop_value),
            "classifier_back": FromView(self, View.classifier_back),
            "classifier_focus_prop_val": FromView(self, View.classifier_focus_prop_val),
            "classifier_reverse": FromView(self, View.classifier_reverse, True),
            "classifier_select_group": FromView(self, View.classifier_select_group),
            "confirm_unique_moves": FromAlgo(self, Algo.confirm_unique_moves, True),
            "convert_prop_multiplicity": FromDb(self, Db.prop_type_set_multiple),
            "create_prop_type": FromDb(self, Db.prop_type_add),
            "delete_property_values": FromAlgo(self, Algo.delete_property_values),
            "delete_video": FromOps(self, Ops.delete_video),
            "delete_video_entry": FromDb(self, Db.video_entry_del),
            "describe_prop_types": FromDb(self, Db.get_prop_types, True),
            "replace_property_values": FromAlgo(self, Algo.replace_property_values),
            "fill_property_with_terms": FromAlgo(self, Algo.fill_property_with_terms),
            "get_database_names": FromApp(self, Application.get_database_names, True),
            "get_language_names": FromApp(self, Application.get_language_names, True),
            "move_property_values": FromAlgo(self, Algo.move_property_values),
            "open_random_video": FromView(self, View.choose_random_video, True),
            "open_video": FromOps(self, Ops.open_video),
            "mark_as_read": FromOps(self, Ops.mark_as_read, True),
            "remove_prop_type": FromDb(self, Db.prop_type_del),
            "rename_database": FromDb(self, Db.rename),
            "rename_prop_type": FromDb(self, Db.prop_type_set_name),
            "rename_video": FromOps(self, Ops.change_video_file_title),
            "set_group": FromView(self, View.set_group),
            "set_groups": FromView(self, View.set_groups),
            "set_search": FromView(self, View.set_search),
            "set_similarities": FromOps(self, Ops.set_similarities_from_list),
            "set_sorting": FromView(self, View.set_sort),
            "set_sources": FromView(self, View.set_sources),
            "set_video_folders": FromOps(self, Ops.set_folders),
            "set_video_moved": FromOps(self, Ops.move_video_entry),
            "confirm_move": FromOps(self, Ops.move_video_entry),
            "set_video_properties": FromDb(self, Db.video_entry_set_tags),
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
    def get_constants(self) -> dict[str, Any]:
        return self._constants

    # cannot make proxy ?
    def set_language(self, name) -> dict[str, str]:
        return language_to_dict(self.application.open_language_from_name(name))

    # cannot make proxy ?
    def backend(self, page_size, page_number, selector=None) -> dict[str, Any]:
        """Return backend state."""
        database_context = self.get_python_backend(page_size, page_number, selector)
        return database_context.json()

    def get_python_backend(
        self, page_size: int, page_number: int, selector: dict | None = None
    ) -> DatabaseContext:
        if selector is not None and isinstance(selector, dict):
            selector = Selector.parse_dict(selector)
        context = self.database.provider.get_current_state(
            page_size, page_number, selector
        )
        return DatabaseContext(
            name=self.database.get_name(),
            folders=sorted(self.database.get_folders()),
            prop_types=self.database.get_prop_types(),
            view=context,
        )

    # cannot make proxy ?
    def classifier_concatenate_path(self, to_property) -> None:
        path = self.database.provider.get_classifier_path()
        from_property = self.database.provider.get_grouping().field
        self.database.provider.set_classifier_path([])
        self.database.provider.set_group(0)
        alg = Algo(self.database)
        alg.move_property_values(path, from_property, to_property, concatenate=True)

    def playlist(self) -> str:
        db = self.database
        pv = db.provider
        ops = Ops(db)
        return str(
            create_xspf_playlist(
                map(ops.get_video_filename, pv.get_view_indices())
            ).open()
        )

    def open_containing_folder(self, video_id: int) -> str:
        ops = Ops(self.database)
        return str(ops.get_video_filename(video_id).locate_file())
