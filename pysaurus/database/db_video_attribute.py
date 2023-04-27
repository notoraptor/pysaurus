from abc import abstractmethod
from typing import Any, Dict, List, Tuple

from pysaurus.video import Video


class _DbVideoAttribute:
    __slots__ = "database", "__iteration", "__values"

    def __init__(self, database):
        self.database = database
        self.__iteration = -1
        self.__values = {}  # type: Dict[Video, Any]

    def __call__(self, video: Video):
        if self.__iteration != self.database.iteration:
            self.__values.clear()
            self._update()
            self.__iteration = self.database.iteration
        if video not in self.__values:
            self.__values[video] = self._get(video)
        return self.__values[video]

    @abstractmethod
    def _update(self):
        raise NotImplementedError()

    @abstractmethod
    def _get(self, video: Video):
        raise NotImplementedError()


class _MoveKey:
    __slots__ = "key", "string"

    def __init__(self, video):
        self.key = (video.file_size, video.duration, video.duration_time_base)
        self.string = f"{video.size}, {video.length}"

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return isinstance(other, _MoveKey) and self.key == other.key

    def __lt__(self, other):
        return self.key < other.key

    def __str__(self):
        return self.string


class PotentialMoveAttribute(_DbVideoAttribute):
    __slots__ = "potential_moves", "move_groups"

    def __init__(self, database):
        super().__init__(database)
        self.potential_moves: Dict[Video, List[dict]] = {}
        self.move_groups: Dict[Video, str] = {}

    def _update(self):
        self.potential_moves.clear()
        self.move_groups.clear()
        groups: Dict[_MoveKey, Tuple[List[Video], List[Video]]] = {}
        for video in self.database.get_cached_videos("readable"):
            groups.setdefault(_MoveKey(video), ([], []))[video.found].append(video)
        for key, (not_found, found) in groups.items():
            if not_found and found:
                for video_not_found in not_found:
                    self.potential_moves[video_not_found] = [
                        {"video_id": video.video_id, "filename": str(video.filename)}
                        for video in found
                    ]
                    self.move_groups[video_not_found] = key.string
                for video in found:
                    self.move_groups[video] = key.string

    def _get(self, video: Video):
        return self.move_groups.get(video, None), self.potential_moves.get(video, [])
