from typing import List, Sequence

from pysaurus.database.video_sorting import VideoSorting
from pysaurus.database.video_state import VideoState
from pysaurus.database.viewport.layers.layer import Layer
from pysaurus.database.viewport.layers.source_layer import SourceLayer
from pysaurus.database.viewport.viewtools.video_array import VideoArray


class SortLayer(Layer):
    __slots__ = ("__filter",)
    __props__ = ("sorting",)
    DEFAULT_SORT_DEF = ["-date"]
    __video_state_attributes__ = dir(VideoState)

    def __init__(self, database):
        super().__init__(database)
        self.__filter = self.filter_all

    def _choose_filter(self):
        root = self.get_root()
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
        return self.get_parameter("sorting")

    def reset_parameters(self):
        self.set_sorting(self.DEFAULT_SORT_DEF)

    def filter(self, data: Sequence[VideoState]) -> VideoArray:
        return self.__filter(data)

    def filter_all(self, data: Sequence[VideoState]) -> VideoArray:
        print("Sort all")
        sorting = VideoSorting(self.get_sorting())
        return VideoArray(sorted(data, key=lambda video: video.to_comparable(sorting)))

    def filter_separate(self, data: Sequence[VideoState]) -> VideoArray:
        print("Sort separate")
        readable_unreadable = [[], []]  # type: List[List[VideoState]]
        for video_state in data:
            readable_unreadable[video_state.unreadable].append(video_state)
        sorting = VideoSorting(self.get_sorting())
        readable_unreadable[0].sort(key=lambda video: video.to_comparable(sorting))

        if readable_unreadable[1]:
            message = []
            if readable_unreadable[0]:
                message.append(f"{len(readable_unreadable[0])} readable sorted")
            message.append(f"{len(readable_unreadable[1])} unreadable not sorted")
            self.database.set_message(", ".join(message) + ".")

        return VideoArray(readable_unreadable[0] + readable_unreadable[1])

    def remove_from_cache(self, cache: VideoArray, video: VideoState):
        if video in cache:
            cache.remove(video)
