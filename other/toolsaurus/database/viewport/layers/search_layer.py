from typing import Optional

from other.toolsaurus.database.viewport.layers.layer import Layer
from other.toolsaurus.database.viewport.layers.source_layer import SourceLayer
from pysaurus.core import functions
from pysaurus.database.video import Video
from pysaurus.database.video_features import VideoFeatures
from pysaurus.database.viewport.view_tools import Group, SearchDef, VideoArray


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
            return VideoArray(VideoFeatures.find(search_def, data.videos))
        return data.videos

    def __filter_from_root_layer(
        self, search_def: SearchDef, source_layer: SourceLayer, data: Group
    ) -> VideoArray:
        term_to_videos = source_layer.get_index()
        terms = functions.string_to_pieces(search_def.text)
        if search_def.cond == "exact":
            selection_and = set(data.videos)
            for term in terms:
                selection_and &= term_to_videos.get(term, set())
            video_filter = Video.has_terms_exact
            selection = (video for video in selection_and if video_filter(video, terms))
        elif search_def.cond == "and":
            selection = set(data.videos)
            for term in terms:
                selection &= term_to_videos.get(term, set())
        elif search_def.cond == "id":
            (term,) = terms
            video_id = int(term)
            selection = (video for video in data.videos if video.video_id == video_id)
        else:  # search_def.cond == 'or'
            selection = set(term_to_videos.get(terms[0], set()))
            for term in terms[1:]:
                selection |= term_to_videos.get(term, set())
            selection &= set(data.videos)
        return VideoArray(selection)

    def _remove_from_cache(self, cache: VideoArray, video: Video):
        if video in cache:
            cache.remove(video)
