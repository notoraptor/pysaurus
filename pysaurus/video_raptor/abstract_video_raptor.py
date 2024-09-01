from abc import abstractmethod

from pysaurus.core.parallelization import Job


class AbstractVideoRaptor:
    __slots__ = ()
    RETURNS_SHORT_KEYS = True

    @abstractmethod
    def collect_video_info(self, job: Job) -> list:
        pass
