import inspect
import random
from typing import Any, Optional

from pysaurus.application import exceptions
from pysaurus.application.application import Application
from pysaurus.application.language.default_language import language_to_dict
from pysaurus.core import functions
from pysaurus.core.classes import Selector, StringPrinter
from pysaurus.core.constants import PYTHON_DEFAULT_SOURCES
from pysaurus.core.file_utils import create_xspf_playlist
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase as Db
from pysaurus.database.database_algorithms import DatabaseAlgorithms as Algo
from pysaurus.database.database_operations import DatabaseOperations as Ops
from pysaurus.dbview.view_context import ViewContext
from pysaurus.interface.api.api_utils.proxy_feature import (
    FromAlgo,
    FromApp,
    FromDb,
    FromOps,
    ProxyFeature,
)
from pysaurus.video.database_context import DatabaseContext


class FeatureAPI:
    __slots__ = (
        "notifier",
        "application",
        "database",
        "view",
        "_proxies",
        "_constants",
    )

    def __init__(self, notifier):
        self.notifier = notifier
        self.application = Application(self.notifier)
        self.database: Db | None = None
        self.view = ViewContext()
        self._constants = {
            "PYTHON_DEFAULT_SOURCES": PYTHON_DEFAULT_SOURCES,
            "PYTHON_APP_NAME": self.application.app_name,
            "PYTHON_FEATURE_COMPARISON": True,
            "PYTHON_LANG": "english",
            "PYTHON_LANGUAGE": "english",
        }
        # We must return value for proxy ending with "!"
        self._proxies: dict[str, str | ProxyFeature] = {
            "apply_on_prop_value": FromOps(self, Ops.apply_on_prop_value),
            "confirm_unique_moves": FromAlgo(self, Algo.confirm_unique_moves, True),
            "convert_prop_multiplicity": FromDb(self, Db.prop_type_set_multiple),
            "create_prop_type": FromDb(self, Db.prop_type_add),
            "delete_property_values": FromAlgo(self, Algo.delete_property_values),
            "delete_video": FromOps(self, Ops.delete_video),
            "delete_video_entry": FromDb(self, Db.video_entry_del),
            "trash_video": FromOps(self, Ops.trash_video),
            "describe_prop_types": FromDb(self, Db.get_prop_types, True),
            "replace_property_values": FromAlgo(self, Algo.replace_property_values),
            "fill_property_with_terms": FromAlgo(self, Algo.fill_property_with_terms),
            "get_database_names": FromApp(self, Application.get_database_names, True),
            "get_language_names": FromApp(self, Application.get_language_names, True),
            "move_property_values": FromAlgo(self, Algo.move_property_values),
            "open_video": FromOps(self, Ops.open_video),
            "mark_as_read": FromOps(self, Ops.mark_as_read, True),
            "remove_prop_type": FromDb(self, Db.prop_type_del),
            "rename_database": FromDb(self, Db.rename),
            "rename_prop_type": FromDb(self, Db.prop_type_set_name),
            "rename_video": FromOps(self, Ops.change_video_file_title),
            "set_similarities": FromOps(self, Ops.set_similarities_from_list),
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

    # View methods (previously FromView proxies)

    def set_sources(self, *args) -> None:
        self.view.set_sources(*args)

    def set_groups(self, *args, **kwargs) -> None:
        self.view.set_grouping(*args, **kwargs)

    def set_group(self, group_id) -> None:
        self.view.set_group(group_id)

    def set_search(self, *args) -> None:
        self.view.set_search(*args)

    def set_sorting(self, sorting) -> None:
        self.view.set_sort(sorting)

    def classifier_select_group(self, group_id) -> None:
        result = self.database.query_videos(self.view, 1, 0)
        value = result.result_groups[group_id].get_value()
        self.view.classifier_select(value)

    def classifier_back(self) -> None:
        self.view.classifier_back()

    def classifier_reverse(self) -> list:
        return self.view.classifier_reverse()

    def classifier_focus_prop_val(self, prop_name, field_value) -> None:
        self.view.set_grouping(
            field=prop_name,
            is_property=True,
            sorting="count",
            reverse=True,
            allow_singletons=True,
        )
        result = self.database.query_videos(self.view, 1, 0)
        group_id = result.result_groups.lookup_index(field_value)
        value = result.result_groups[group_id].get_value()
        self.view.classifier_select(value)

    def apply_on_view(self, selector, db_fn_name, *db_fn_args):
        result = self.database.query_videos(self.view, None, None)
        view_indices = [v.video_id for v in result.result]
        ops = Ops(self.database)
        callable_methods = {
            "count_property_values": ops.count_property_for_videos,
            "edit_property_for_videos": ops.update_property_for_videos,
        }
        return callable_methods[db_fn_name](
            functions.apply_selector_to_data(selector, view_indices), *db_fn_args
        )

    def open_random_video(self, open_video=True) -> str:
        video_indices = []
        for path in self.view.sources:
            where = {flag: True for flag in path}
            if "not_found" in where or "unreadable" in where:
                continue
            where["found"] = True
            where["readable"] = True
            where["watched"] = False
            video_indices.extend(
                video.video_id
                for video in self.database.get_videos(include=["video_id"], where=where)
            )
        if not video_indices:
            raise exceptions.NoVideos()
        video_id = video_indices[random.randrange(len(video_indices))]
        self.view.set_grouping(None)
        self.view.set_search(str(video_id), "id")
        ops = Ops(self.database)
        if open_video:
            ops.open_video(video_id)
        return ops.get_video_filename(video_id).path

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
        context = self.database.query_videos(
            self.view, page_size, page_number, selector
        )
        return DatabaseContext(
            name=self.database.get_name(),
            folders=sorted(self.database.get_folders()),
            prop_types=self.database.get_prop_types(),
            view=context,
        )

    # cannot make proxy ?
    def classifier_concatenate_path(self, to_property) -> None:
        path = list(self.view.classifier)
        from_property = self.view.grouping.field
        self.view.classifier = []
        self.view.group = 0
        alg = Algo(self.database)
        alg.move_property_values(path, from_property, to_property, concatenate=True)

    def playlist(self) -> str:
        db = self.database
        ops = Ops(db)
        result = db.query_videos(self.view, None, None)
        view_indices = [v.video_id for v in result.result]
        return str(
            create_xspf_playlist(map(ops.get_video_filename, view_indices)).open()
        )

    def set_similarities_reencoded(
        self, video_indices: list[int], similarities: list[int | None]
    ) -> None:
        ops = Ops(self.database)
        ops.set_similarities_from_list(
            video_indices, similarities, field="similarity_id_reencoded"
        )

    def open_containing_folder(self, video_id: int) -> str:
        ops = Ops(self.database)
        return str(ops.get_video_filename(video_id).locate_file())
