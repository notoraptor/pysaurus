from abc import abstractmethod
from typing import Any, Dict

from pysaurus.database.video import Video


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
    __slots__ = "fields", "min", "max"

    QUALITY_FIELDS = (
        ("quality_compression", 6),
        ("height", 5),
        ("width", 4),
        ("raw_seconds", 3),
        ("frame_rate", 2),
        ("file_size", 1),
        ("audio_bit_rate", 0.5),
    )

    def __init__(self, database):
        super().__init__(database)
        self.fields = tuple(t[0] for t in self.QUALITY_FIELDS)
        self.min = {}
        self.max = {}

    def _update(self):
        videos = list(self.database.get_videos("readable"))
        if not videos:
            self.min.clear()
            self.max.clear()
            return
        self.min = {
            field: min(getattr(video, field) for video in videos)
            for field in self.fields
        }
        self.max = {
            field: max(getattr(video, field) for video in videos)
            for field in self.fields
        }

    def _get(self, video: Video):
        total_level = 0
        qualities = {}
        for field, level in self.QUALITY_FIELDS:
            value = getattr(video, field)
            min_value = self.min[field]
            max_value = self.max[field]
            if min_value == max_value:
                assert value == min_value, (value, min_value)
                quality = 0
            else:
                quality = (value - min_value) / (max_value - min_value)
                assert 0 <= quality <= 1, (quality, field, value, min_value, max_value)
            qualities[field] = quality * level
            total_level += level
        return sum(qualities.values()) * 100 / total_level


class _MoveKey:
    __slots__ = "key", "string"

    def __init__(self, video):
        self.key = (video.file_size, video.duration, video.duration_time_base)
        self.string = f"{video.size}, {video.length}"

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key

    def __lt__(self, other):
        return self.key < other.key

    def __str__(self):
        return self.string


class PotentialMoveAttribute(_DbVideoAttribute):
    __slots__ = "potential_moves", "move_groups"

    def __init__(self, database):
        super().__init__(database)
        self.potential_moves = {}
        self.move_groups = {}

    def _update(self):
        self.potential_moves.clear()
        self.move_groups.clear()
        groups = {}
        for video in self.database.get_videos("readable"):
            groups.setdefault(_MoveKey(video), ([], []))[video.found].append(video)
        for key, (not_found, found) in groups.items():
            if not_found and found:
                for video_not_found in not_found:
                    self.potential_moves[video_not_found] = found
                    self.move_groups[video_not_found] = key
                for video in found:
                    self.move_groups[video] = key

    def _get(self, video: Video):
        return self.move_groups.get(video, None), self.potential_moves.get(video, ())
