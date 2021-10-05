from abc import abstractmethod
from typing import Any, Dict

from pysaurus.database.video import Video


class DbVideoAttribute:
    __slots__ = "database", "__iteration", "__values"

    def __init__(self, database):
        self.database = database
        self.__iteration = -1
        self.__values = {}  # type: Dict[Video, Any]

    def __call__(self, video: Video):
        if self.__iteration != self.database.iteration:
            self.update()
            self.__iteration = self.database.iteration
        if video not in self.__values:
            self.__values[video] = self.get(video)
        return self.__values[video]

    @abstractmethod
    def update(self):
        raise NotImplementedError()

    @abstractmethod
    def get(self, video: Video):
        raise NotImplementedError()


class QualityAttribute(DbVideoAttribute):
    __slots__ = "fields", "min", "max"

    def __init__(self, database):
        super().__init__(database)
        self.fields = tuple(t[0] for t in Video.QUALITY_FIELDS)
        self.min = {}
        self.max = {}

    def update(self):
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

    def get(self, video: Video):
        total_level = 0
        qualities = {}
        for field, level in Video.QUALITY_FIELDS:
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


class PotentialMoveAttribute(DbVideoAttribute):
    __slots__ = "potential_moves", "move_groups"

    def __init__(self, database):
        super().__init__(database)
        self.potential_moves = {}
        self.move_groups = {}

    def update(self):
        self.potential_moves.clear()
        groups = {}
        for video in self.database.get_videos("readable"):
            key = (video.file_size, video.duration, video.duration_time_base)
            groups.setdefault(key, ([], []))[video.found].append(video)
        move_id = 0
        for not_found, found in groups.values():
            if not_found and found:
                for video_not_found in not_found:
                    self.potential_moves[video_not_found] = found
                    self.move_groups[video_not_found] = move_id
                for video in found:
                    self.move_groups[video] = move_id
                move_id += 1

    def get(self, video: Video):
        return self.move_groups.get(video, None), self.potential_moves.get(video, ())
