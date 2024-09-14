import logging
from typing import Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


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


class PotentialMoveAttribute:
    __slots__ = ("potential_moves", "move_groups", "force_update", "database")

    def __init__(self, database):
        from pysaurus.database.abstract_database import AbstractDatabase

        self.database: AbstractDatabase = database
        self.potential_moves: Dict[int, List[dict]] = {}
        self.move_groups: Dict[int, str] = {}
        self.force_update = True

    def __call__(self, video_id: Optional[int]):
        self._update()
        return self.move_groups.get(video_id, None), self.potential_moves.get(
            video_id, []
        )

    def _update(self):
        if not self.force_update:
            return
        self.force_update = False
        logger.debug(f"[{type(self).__name__}] moves updated.")
        self.potential_moves.clear()
        self.move_groups.clear()
        groups: Dict[_MoveKey, Tuple[List[dict], List[dict]]] = {}
        videos = self.database.get_videos(
            include=(
                "duration",
                "duration_time_base",
                "file_size",
                "filename",
                "found",
                "length",
                "size",
                "video_id",
            ),
            where={"readable": True},
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

    def get_moves(self) -> Iterable[Tuple[int, List[dict]]]:
        self._update()
        return self.potential_moves.items()
