from typing import Callable, Sequence

import flet as ft

from pysaurus.core.constants import PYTHON_DEFAULT_SOURCES, VIDEO_DEFAULT_SORTING
from pysaurus.properties.properties import PropTypeDesc
from pysaurus.video.javascript_video import JavascriptVideo


class DatabaseStateWrapper:
    __slots__ = ("state",)

    def __init__(self, state: dict):
        self.state = state

    @property
    def name(self) -> str:
        return self.state["name"]

    @property
    def folders(self) -> list[str]:
        return self.state["folders"]


class StateWrapper:
    __slots__ = ("state",)

    def __init__(self, state: dict):
        self.state = state

    @property
    def database(self) -> DatabaseStateWrapper:
        return DatabaseStateWrapper(self.state["database"])

    @property
    def prop_types(self) -> list[PropTypeDesc]:
        return [PropTypeDesc(desc) for desc in self.state["prop_types"]]

    @property
    def nb_source_videos(self) -> int:
        return self.state["nbSourceVideos"]

    @property
    def group_def(self) -> dict | None:
        return self.state["groupDef"]

    @property
    def videos(self) -> list[JavascriptVideo]:
        return [JavascriptVideo(data) for data in self.state["videos"]]

    @property
    def page_size(self) -> int:
        return self.state["pageSize"]

    @property
    def page_number(self) -> int:
        return self.state["pageNumber"]

    @property
    def nb_pages(self) -> int:
        return self.state["nbPages"]

    @property
    def nb_videos(self) -> int:
        return self.state["nbVideos"]

    @property
    def nb_view_videos(self) -> int:
        return self.state["nbViewVideos"]

    @property
    def valid_size(self) -> str:
        return self.state["validSize"]

    @property
    def valid_length(self) -> str:
        return self.state["validLength"]

    @property
    def sources(self) -> Sequence[Sequence[str]]:
        return self.state["sources"]

    @property
    def path(self) -> list[str | bool | int | float]:
        return self.state["path"]

    @property
    def search_def(self) -> dict | None:
        return self.state["searchDef"]

    @property
    def sorting(self) -> list[str]:
        return self.state["sorting"]

    def source_is_set(self) -> bool:
        return self.sources != PYTHON_DEFAULT_SOURCES

    def group_is_set(self) -> bool:
        return bool(self.group_def)

    def search_is_set(self) -> bool:
        return bool(self.search_def)

    def sort_is_set(self) -> bool:
        return self.sorting != VIDEO_DEFAULT_SORTING

    def is_filtered(self) -> bool:
        return (
            self.source_is_set()
            or self.group_is_set()
            or self.search_is_set()
            or self.sort_is_set()
        )

    def is_grouped_by_moves(self) -> bool:
        return self.group_def and self.group_def["field"] == "move_id"

    def is_grouped_by_similarity(self) -> bool:
        return self.group_def and self.group_def["field"] == "similarity_id"

    def common_fields(self) -> dict[str, bool]:
        return (self.is_grouped_by_similarity() and self.group_def["common"]) or {}

    def can_open_random_video(self) -> bool:
        return not self.all_not_found() and self.nb_source_videos

    def all_not_found(self) -> bool:
        return all("not_found" in source for source in self.sources)

    def get_multiple_string_prop_types(self) -> list[PropTypeDesc]:
        return [desc for desc in self.prop_types if desc.multiple and desc.type is str]


class Shortcut:
    __slots__ = ("ctrl", "alt", "shift", "key")

    def __init__(self, shortcut: str):
        pieces = [piece.lower() for piece in shortcut.split("+")]
        special_keys = set(pieces[:-1])
        self.ctrl = "ctrl" in special_keys
        self.alt = "alt" in special_keys
        self.shift = "shift" in special_keys or "maj" in special_keys
        self.key = pieces[-1]

    def __hash__(self):
        return hash(self.tuple())

    def __eq__(self, other):
        assert isinstance(other, Shortcut)
        return self.tuple() == other.tuple()

    def tuple(self):
        return self.ctrl, self.alt, self.shift, self.key


class Action:
    __slots__ = ("name", "shortcut", "title", "callback", "filter")

    def __init__(
        self,
        name: str,
        shortcut: str,
        title: str,
        callback: Callable[[], None],
        condition: Callable[[], bool] = None,
    ):
        self.name = name
        self.shortcut = Shortcut(shortcut)
        self.title = title
        self.callback = callback
        self.filter = condition

    def execute(self):
        if self.filter is None or self.filter():
            self.callback()

    def on_click(self, e):
        return self.execute()


class Actions:
    __slots__ = ("actions", "shortcut_to_action", "name_to_action")

    def __init__(self, actions: Sequence[Action]):
        assert len({action.name for action in actions}) == len(actions)
        assert len({action.shortcut for action in actions}) == len(actions)
        assert len({action.title for action in actions}) == len(actions)
        self.actions = actions
        self.name_to_action = {action.name: action for action in actions}
        self.shortcut_to_action = {
            action.shortcut.tuple(): action for action in actions
        }

    def __getitem__(self, name: str) -> Action:
        return self.name_to_action[name]

    def on_keyboard_event(self, e: ft.KeyboardEvent):
        shortcut_tuple = (e.ctrl, e.alt, e.shift, e.key.lower())
        if shortcut_tuple in self.shortcut_to_action:
            self.shortcut_to_action[shortcut_tuple].execute()
