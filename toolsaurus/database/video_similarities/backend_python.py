from typing import List

from pysaurus.core import notifications
from pysaurus.core.constants import VIDEO_BATCH_SIZE
from pysaurus.core.notifier import Notifier
from pysaurus.core.profiling import Profiler
from pysaurus.database.miniature_tools.miniature import Miniature
from pysaurus.database.video_similarities.backend_python import (
    compare_faster,
    SIMPLE_MAX_PIXEL_DISTANCE,
)


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
    job_notifier = notifications.Jobs.native_comparisons(nb_sequences, notifier)
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
