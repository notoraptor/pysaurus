from abc import ABCMeta, abstractmethod
from typing import Iterable, Sequence

from pysaurus.core.components import AbsolutePath
from pysaurus.video import Video


class AbstractVideoIndexer(metaclass=ABCMeta):
    __slots__ = ()

    def update_videos(self, videos: Iterable[Video]):
        for video in videos:
            self._update_video(video)

    def remove_videos(self, videos: Iterable[Video]):
        for video in videos:
            self._remove_filename(video.filename)

    def close(self):
        """Close indexer."""
        if self._can_save():
            self._save()

    def _update_video(self, video: Video):
        self._remove_filename(video.filename)
        self._add_video(video)

    @abstractmethod
    def _can_save(self) -> bool:
        return False

    @abstractmethod
    def _save(self):
        raise NotImplementedError()

    @abstractmethod
    def _load(self):
        raise NotImplementedError()

    @abstractmethod
    def build(self, videos: Iterable[Video]):
        raise NotImplementedError()

    @abstractmethod
    def _add_video(self, video: Video):
        raise NotImplementedError()

    @abstractmethod
    def _remove_filename(self, filename: AbsolutePath) -> None:
        raise NotImplementedError()

    @abstractmethod
    def query_and(
        self, filenames: Iterable[AbsolutePath], terms: Sequence[str]
    ) -> Iterable[AbsolutePath]:
        pass

    @abstractmethod
    def query_or(
        self, filenames: Iterable[AbsolutePath], terms: Sequence[str]
    ) -> Iterable[AbsolutePath]:
        pass

    @abstractmethod
    def query_flags(
        self, filenames: Iterable[AbsolutePath], *flags, **forced_flags
    ) -> Iterable[AbsolutePath]:
        pass
