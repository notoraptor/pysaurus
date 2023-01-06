from typing import List, Optional

from pysaurus.core.constants import VIDEO_BATCH_SIZE
from pysaurus.core.functions import camel_case_to_snake_case
from pysaurus.core.job_notifications import JobStep, JobToDo
from pysaurus.core.notifier import Notifier
from pysaurus.core.profiling import Profiler
from pysaurus.database.miniature_tools.miniature import Miniature
from pysaurus.database.video_similarities.backend_python import (
    SIMPLE_MAX_PIXEL_DISTANCE,
    compare_faster,
)


class JobNotifications:
    __slots__ = "name", "notifier"
    __kind__ = "datas"

    def __init__(self, total: int, notifier, title: str = None, pretty_total=None):
        name = camel_case_to_snake_case(type(self).__name__).replace("_", " ")
        if title is None:
            if pretty_total is None:
                pretty_total = f"{total} {self.__kind__}"
            title = f"{name} ({pretty_total})"
        self.name = name
        self.notifier = notifier
        self.notifier.notify(JobToDo(self.name, total, title))
        if total:
            self.notifier.notify(JobStep(self.name, None, 0, total, title=title))

    def progress(
        self,
        channel: Optional[str],
        channel_step: int,
        channel_size: int,
        *,
        title: str = None,
    ):
        self.notifier.notify(
            JobStep(self.name, channel, channel_step, channel_size, title=title)
        )


class CompareMiniatures(JobNotifications):
    __slots__ = ()
    __kind__ = "videos (C++ comparison)"


def internal_classify_similarities_directed(
    sequences: List[Miniature],
    nb_sequences: int,
    i_from: int,
    i_to: int,
    width: int,
    height: int,
    edges,
    sim_limit,
    maximum_distance_score,
):
    for i in range(i_from, min(i_to, nb_sequences)):
        for j in range(i + 1, nb_sequences):
            if edges[i * nb_sequences + j]:
                edges[i * nb_sequences + j] = (
                    compare_faster(
                        sequences[i],
                        sequences[j],
                        width,
                        height,
                        maximum_distance_score,
                    )
                    >= sim_limit
                )


def classify_similarities_directed_old(
    miniatures: List[Miniature], edges, sim_limit, notifier: Notifier
):
    nb_sequences = len(miniatures)
    width = miniatures[0].width
    height = miniatures[0].height
    maximum_distance_score = SIMPLE_MAX_PIXEL_DISTANCE * width * height
    job_notifier = CompareMiniatures(nb_sequences, notifier)
    with Profiler("Finding similar images using simpler NATIVE comparison.", notifier):
        cursor = 0
        while cursor < nb_sequences:
            i_from = cursor
            i_to = cursor + VIDEO_BATCH_SIZE
            internal_classify_similarities_directed(
                miniatures,
                nb_sequences,
                i_from,
                i_to,
                width,
                height,
                edges,
                sim_limit,
                maximum_distance_score,
            )
            job_notifier.progress(None, min(i_to, nb_sequences), nb_sequences)
            cursor = i_to
        job_notifier.progress(None, nb_sequences, nb_sequences)
