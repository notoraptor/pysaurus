from typing import Sequence

from pysaurus.core.database.video import Video
from pysaurus.core.database.viewport.layers.layer import Layer
from pysaurus.core.database.viewport.viewtools.video_array import VideoArray


class SortLayer(Layer):
    __slots__ = ()
    __props__ = ("sorting",)
    DEFAULT_SORT_DEF = ["-date"]

    def set_sorting(self, sorting: Sequence[str]):
        self._set_parameters(
            sorting=list(sorting) if sorting else self.DEFAULT_SORT_DEF
        )

    def get_sorting(self):
        return self.get_parameter("sorting")

    def reset_parameters(self):
        self.set_sorting(self.DEFAULT_SORT_DEF)

    def filter(self, data: Sequence[Video]) -> VideoArray:
        sorting = self.get_sorting()
        return VideoArray(sorted(data, key=lambda video: video.to_comparable(sorting)))

    def remove_from_cache(self, cache: VideoArray, video: Video):
        if video in cache:
            cache.remove(video)
