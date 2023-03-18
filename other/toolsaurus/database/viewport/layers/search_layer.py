from typing import Optional

from other.toolsaurus.database.viewport.layers.layer import Layer
from other.toolsaurus.database.viewport.layers.source_layer import SourceLayer
from other.toolsaurus.modules import OtherVideoFeatures
from pysaurus.database.viewport.view_tools import Group, SearchDef, VideoArray
from pysaurus.video.video import Video


class SearchLayer(Layer):
    __slots__ = ()
    __props__ = ("search",)
    DEFAULT_SEARCH_DEF = SearchDef()

    def set_search(self, text: Optional[str], cond: Optional[str]):
        self._set_parameters(search=SearchDef(text, cond))

    def get_search(self) -> SearchDef:
        return self._get_parameter("search")

    def reset_parameters(self):
        self._set_parameters(search=self.DEFAULT_SEARCH_DEF)

    def _filter(self, data: Group) -> VideoArray:
        search_def = self.get_search()
        if search_def:
            root = self._get_root()
            if isinstance(root, SourceLayer):
                return self.__filter_from_root_layer(search_def, root, data)
            return VideoArray(OtherVideoFeatures.find(search_def, data.videos))
        return data.videos

    def __filter_from_root_layer(
        self, search_def: SearchDef, source_layer: SourceLayer, data: Group
    ) -> VideoArray:
        return VideoArray(
            self.database.search(search_def.text, search_def.cond, data.videos)
        )

    def _remove_from_cache(self, cache: VideoArray, video: Video):
        if video in cache:
            cache.remove(video)
