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


class QualityAttribute(_DbVideoAttribute):
    __slots__ = "min", "max"

    QUALITY_FIELDS = (
        ("quality_compression", 6),  # 0, 1 ?
        ("height", 5),  # 0, 16/9 4k => 2160 ?
        ("width", 4),  # 0, 16/9 4k => 3840 ?
        ("raw_seconds", 3),  # 0, 30 minutes ?
        ("frame_rate", 2),  # 0, 60 fps ?
        ("file_size", 1),
        ("audio_bit_rate", 0.5),
    )
    FIELDS = tuple(t[0] for t in QUALITY_FIELDS)
    TOTAL_LEVEL = sum(t[1] for t in QUALITY_FIELDS)

    def __init__(self, database):
        super().__init__(database)
        self.min = []
        self.max = []

    def _update(self):
        videos = list(self.database.get_cached_videos("readable"))
        if not videos:
            self.min.clear()
            self.max.clear()
            return
        self.min = [
            min(getattr(video, field) for video in videos) for field in self.FIELDS
        ]
        self.max = [
            max(getattr(video, field) for video in videos) for field in self.FIELDS
        ]

    def _get(self, video: Video):
        if video.unreadable:
            return 0
        # REFERENCE: For each field:
        # if min_value == max_value:
        #   assert value == min_value, (value, min_value)
        #   quality = 0
        # else:
        #   quality = (value - min_value) / (max_value - min_value)
        #   assert 0 <= quality <= 1, (quality, field, value, min_value, max_value)
        return (
            sum(
                (
                    0
                    if self.min[i] == self.max[i]
                    else (getattr(video, field) - self.min[i])
                    / (self.max[i] - self.min[i])
                )
                * level
                for i, (field, level) in enumerate(self.QUALITY_FIELDS)
            )
            * 100
            / self.TOTAL_LEVEL
        )


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
