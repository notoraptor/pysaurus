from typing import Dict, Iterable, Sequence, Set

from pysaurus.core.components import AbsolutePath
from pysaurus.core.profiling import Profiler
from pysaurus.database.database import Database
from pysaurus.database.video import Video
from pysaurus.database.viewport.layers.layer import Layer


class SourceLayer(Layer):
    __slots__ = ()
    __props__ = ("sources",)
    _cache: Dict[AbsolutePath, Video]
    DEFAULT_SOURCE_DEF = [("readable",)]

    def __init__(self, database):
        super().__init__(database)

    def set_sources(self, paths: Sequence[Sequence[str]] = None):
        if paths is None:
            self.reset_parameters()
        else:
            valid_paths = set()
            for path in paths:
                path = tuple(path)
                if path not in valid_paths:
                    assert len(set(path)) == len(path)
                    assert all(Video.is_flag(flag) for flag in path)
                    valid_paths.add(path)
            if valid_paths:
                self._set_parameters(sources=sorted(valid_paths))

    def get_sources(self):
        return self.get_parameter("sources")

    def reset_parameters(self):
        self.set_sources(self.DEFAULT_SOURCE_DEF)

    def filter(self, database: Database) -> Dict[AbsolutePath, Video]:
        source = []
        for path in self.get_sources():
            source.extend(database.get_videos(*path))
        source_dict = {video.filename: video for video in source}
        assert len(source_dict) == len(source), (len(source_dict), len(source))
        return source_dict

    def remove_from_cache(self, cache: Dict[AbsolutePath, Video], vs: Video):
        assert vs.filename in cache, len(cache)
        del cache[vs.filename]

    def videos(self):
        return self._cache.values()

    def get_index(self):
        return self.database.indexer.get_index()
