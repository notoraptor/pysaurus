from typing import List, Sequence

from other.toolsaurus.database.viewport.layers.layer import Layer
from other.toolsaurus.database.viewport.layers.source_layer import SourceLayer
from pysaurus.database.video import Video
from pysaurus.database.video_sorting import VideoSorting
from pysaurus.database.viewport.view_tools import VideoArray


class SortLayer(Layer):
    __slots__ = ("__filter",)
    __props__ = ("sorting",)
    DEFAULT_SORT_DEF = ["-date"]
    __video_state_attributes__ = dir(Video)

    def __init__(self, database):
        super().__init__(database)
        self.__filter = self.filter_all

    def _choose_filter(self):
        root = self._get_root()
        sorting = self.get_sorting()
        if (
            isinstance(root, SourceLayer)
            and any("unreadable" in source for source in root.get_sources())
            and any(sort[1:] not in self.__video_state_attributes__ for sort in sorting)
        ):
            self.__filter = self.filter_separate
        else:
            self.__filter = self.filter_all

    def set_sorting(self, sorting: Sequence[str]):
        self._set_parameters(
            sorting=list(sorting) if sorting else self.DEFAULT_SORT_DEF
        )
        self._choose_filter()

    def set_data(self, data):
        super().set_data(data)
        self._choose_filter()

    def get_sorting(self):
        return self._get_parameter("sorting")

    def reset_parameters(self):
        self.set_sorting(self.DEFAULT_SORT_DEF)

    def _filter(self, data: Sequence[Video]) -> VideoArray:
        return self.__filter(data)

    def filter_all(self, data: Sequence[Video]) -> VideoArray:
        print("Sort all")
        sorting = VideoSorting(self.get_sorting())
        return VideoArray(sorted(data, key=lambda video: video.to_comparable(sorting)))

    def filter_separate(self, data: Sequence[Video]) -> VideoArray:
        print("Sort separate")
        readable_unreadable = [[], []]  # type: List[List[Video]]
        for video_state in data:
            readable_unreadable[video_state.unreadable].append(video_state)
        sorting = VideoSorting(self.get_sorting())
        readable_unreadable[0].sort(key=lambda video: video.to_comparable(sorting))

        if readable_unreadable[1]:
            message = []
            if readable_unreadable[0]:
                message.append(
                    self.database.lang.message_count_readable_sorted.format(
                        count=len(readable_unreadable[0])
                    )
                )
            message.append(
                self.database.lang.message_count_unreadable_not_sorted.format(
                    count=len(readable_unreadable[1])
                )
            )

        return VideoArray(readable_unreadable[0] + readable_unreadable[1])

    def _remove_from_cache(self, cache: VideoArray, video: Video):
        if video in cache:
            cache.remove(video)