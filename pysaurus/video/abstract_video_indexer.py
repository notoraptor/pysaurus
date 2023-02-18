from abc import ABCMeta, abstractmethod
from typing import Dict, Iterable, List, Sequence, Set

from pysaurus.core.components import AbsolutePath
from pysaurus.video.video import Video


class AbstractVideoIndexer(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def add_video(self, video: Video):
        pass

    @abstractmethod
    def build(self, videos: Iterable[Video]):
        pass

    @abstractmethod
    def _remove_filename(self, filename: AbsolutePath, pop=False) -> List[str]:
        pass

    def remove_video(self, video: Video):
        self._remove_filename(video.filename)

    def update_video(self, video: Video):
        self.remove_video(video)
        self.add_video(video)

    @abstractmethod
    def replace_path(self, video: Video, old_path: AbsolutePath):
        pass

    @abstractmethod
    def get_index(self) -> Dict[str, Set[AbsolutePath]]:
        pass

    @abstractmethod
    def query_and(
        self, filenames: Iterable[AbsolutePath], terms: Sequence[str]
    ) -> Iterable[AbsolutePath]:
        pass

    @abstractmethod
    def query_exact(
        self, filenames: Iterable[AbsolutePath], terms: Sequence[str]
    ) -> Iterable[AbsolutePath]:
        pass

    @abstractmethod
    def query_or(
        self, filenames: Iterable[AbsolutePath], terms: Sequence[str]
    ) -> Iterable[AbsolutePath]:
        pass
