import logging
from abc import abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


class _DbVideoAttribute:
    __slots__ = "database", "__iteration", "__values"

    def __init__(self, database):
        from pysaurus.database.database import Database

        self.database: Database = database
        self.__iteration = -1
        self.__values: Dict[int, Any] = {}

    def __call__(self, video_id: int):
        if self.__iteration != self.database.iteration:
            self.__values.clear()
            self._update()
            self.__iteration = self.database.iteration
        if video_id not in self.__values:
            self.__values[video_id] = self._get(video_id)
        return self.__values[video_id]

    @abstractmethod
    def _update(self):
        raise NotImplementedError()

    @abstractmethod
    def _get(self, video_id: int):
        raise NotImplementedError()


class _MoveKey:
    __slots__ = "key", "string"

    def __init__(self, video: dict):
        self.key = (video["file_size"], video["duration"], video["duration_time_base"])
        self.string = f"{video['size']}, {video['length']}"

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return isinstance(other, _MoveKey) and self.key == other.key

    def __lt__(self, other):
        return self.key < other.key

    def __str__(self):
        return self.string


class PotentialMoveAttribute(_DbVideoAttribute):
    __slots__ = "potential_moves", "move_groups", "force_update"

    def __init__(self, database):
        super().__init__(database)
        self.potential_moves: Dict[int, List[dict]] = {}
        self.move_groups: Dict[int, str] = {}
        self.force_update = True

    def __call__(self, video_id: Optional[int]):
        if self.force_update:
            self._update()
            self.force_update = False
        return self._get(video_id)

    def _update(self):
        logger.debug(f"[{type(self).__name__}] moves updated.")
        self.potential_moves.clear()
        self.move_groups.clear()
        groups: Dict[_MoveKey, Tuple[List[dict], List[dict]]] = {}
        videos = self.database.select_videos_fields(
            (
                "duration",
                "duration_time_base",
                "file_size",
                "filename",
                "found",
                "length",
                "size",
                "video_id",
            ),
            "readable",
        )
        for video in videos:
            groups.setdefault(_MoveKey(video), ([], []))[video["found"]].append(video)
        for key, (not_found, found) in groups.items():
            if not_found and found:
                for video_not_found in not_found:
                    self.potential_moves[video_not_found["video_id"]] = [
                        {
                            "video_id": video["video_id"],
                            "filename": str(video["filename"]),
                        }
                        for video in found
                    ]
                    self.move_groups[video_not_found["video_id"]] = key.string
                for video in found:
                    self.move_groups[video["video_id"]] = key.string

    def _get(self, video_id: int):
        return self.move_groups.get(video_id, None), self.potential_moves.get(
            video_id, []
        )

    def get_unique_moves(self) -> Iterable[Tuple[int, List[dict]]]:
        self(None)
        return (
            (video_id, moves)
            for video_id, moves in self.potential_moves.items()
            if len(moves) == 1
        )
