from typing import Dict, Sequence, Iterable, Set

from pysaurus.core.components import AbsolutePath
from pysaurus.core.profiling import Profiler
from pysaurus.database.database import Database
from pysaurus.database.video_state import VideoState
from pysaurus.database.viewport.layers.layer import Layer


class SourceLayer(Layer):
    __slots__ = ("index",)
    __props__ = ("sources",)
    _cache: Dict[AbsolutePath, VideoState]
    DEFAULT_SOURCE_DEF = [("readable",)]

    def __init__(self, database):
        super().__init__(database)
        self.index = {}  # type: Dict[str, Set[VideoState]]

    def set_sources(self, paths: Sequence[Sequence[str]] = None):
        if paths is None:
            self.reset_parameters()
        else:
            valid_paths = set()
            for path in paths:
                path = tuple(path)
                if path not in valid_paths:
                    assert len(set(path)) == len(path)
                    assert all(VideoState.is_flag(flag) for flag in path)
                    valid_paths.add(path)
            if valid_paths:
                self._set_parameters(sources=sorted(valid_paths))

    def get_sources(self):
        return self.get_parameter("sources")

    def reset_parameters(self):
        self.set_sources(self.DEFAULT_SOURCE_DEF)

    def filter(self, database: Database) -> Dict[AbsolutePath, VideoState]:
        source = []
        for path in self.get_sources():
            source.extend(database.get_videos(*path))
        source_dict = {video.filename: video for video in source}
        assert len(source_dict) == len(source), (len(source_dict), len(source))
        self.index = self.__index_videos(source)
        return source_dict

    def remove_from_cache(self, cache: Dict[AbsolutePath, VideoState], vs: VideoState):
        assert vs.filename in cache, len(cache)
        for term in vs.terms(as_set=True):
            assert vs in self.index[term], len(self.index[term])
            self.index[term].remove(vs)
            if not self.index[term]:
                del self.index[term]
        del cache[vs.filename]

    def count_videos(self):
        return len(self._cache)

    def videos(self):
        return self._cache.values()

    def update_index(self):
        self.index = self.__index_videos(self._cache.values())

    @classmethod
    @Profiler.profile()
    def __index_videos(cls, videos: Iterable[VideoState]) -> Dict[str, Set[VideoState]]:
        term_to_videos = {}
        for video in videos:
            for term in video.terms():
                term_to_videos.setdefault(term, set()).add(video)
        return term_to_videos