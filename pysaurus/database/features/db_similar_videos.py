import itertools
import logging
from ctypes import Array, c_bool
from typing import List, Set

import numpy as np

from pysaurus.application import exceptions
from pysaurus.core import notifications
from pysaurus.core.fraction import Fraction
from pysaurus.core.functions import compute_nb_couples, get_end_index, get_start_index
from pysaurus.core.informer import Informer
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.miniature.graph import Graph
from pysaurus.miniature.miniature import Miniature
from saurus.language import say

# from collections import deque
logger = logging.getLogger(__name__)

try:
    from pysaurus.video_similarities.alignment_raptor import alignment as backend_sim

    has_cpp = True
except exceptions.CysaurusUnavailable:
    from pysaurus.video_similarities import backend_python as backend_sim

    has_cpp = False
    logger.warning("Using fallback backend for video similarities search.")

FRAC_SIM_LIMIT = Fraction(88, 100)
FRAC_DST_LIMIT = Fraction(1) - FRAC_SIM_LIMIT
SIM_LIMIT = float(FRAC_SIM_LIMIT)
DST_LIMIT = float(FRAC_DST_LIMIT)
GRAY_DEC = float(Fraction(255) * FRAC_DST_LIMIT)


class _NbGroupsClassifier:
    __slots__ = "counts", "groups"

    def __init__(self, counts: List[int], groups: List[List[int]]):
        self.counts = counts
        self.groups = groups

    @classmethod
    def classify(cls, miniatures: List[Miniature], indices: List[int]):
        nb_to_ids = {}
        for i in indices:
            nb_to_ids.setdefault(miniatures[i].group_signature.n, []).append(i)
        nb_then_ids = sorted(nb_to_ids.items(), key=lambda item: item[0])
        return cls([count for count, _ in nb_then_ids], [ids for _, ids in nb_then_ids])


class _GrayClassifier:
    __slots__ = "grays", "classifiers", "j_limit"

    def __init__(self, grays: List[float], classifiers: List[_NbGroupsClassifier]):
        self.grays = grays
        self.classifiers = classifiers
        self.j_limit = [
            get_end_index(grays, grays[i] + GRAY_DEC, i + 1) for i in range(len(grays))
        ]

    def compare_miniature_grays(self):
        """Return sequence of couples of indices of classifiers to cross compare."""
        notifier = Informer.default()
        n = len(self.grays)
        t = self.j_limit
        notifier.task(self.compare_miniature_grays, n, "miniatures")
        for i in range(n):
            for j in range(i + 1, t[i]):
                yield i, j
            if (i + 1) % 1000 == 0:
                notifier.progress(self.compare_miniature_grays, i + 1, n)
        notifier.progress(self.compare_miniature_grays, n, n)

    @classmethod
    def classify(cls, miniatures: List[Miniature], miniature_indices: List[int] = None):
        if miniature_indices is None:
            miniature_indices = list(range(len(miniatures)))

        gray_to_identifiers = {}
        for i in miniature_indices:
            gray_to_identifiers.setdefault(miniatures[i].global_intensity(), []).append(
                i
            )
        gray_to_classifier = {
            gray: _NbGroupsClassifier.classify(miniatures, indices)
            for gray, indices in gray_to_identifiers.items()
        }
        gray_then_classifier = sorted(
            gray_to_classifier.items(), key=lambda item: item[0]
        )
        return cls(
            [float(gray) for gray, _ in gray_then_classifier],
            [classifier for _, classifier in gray_then_classifier],
        )


class DbSimilarVideos:
    __slots__ = ("positions",)

    def __init__(self):
        # self.positions = deque()
        self.positions = None

    def find(self, db, ignore_cache: bool) -> None:
        if ignore_cache:
            return self.find_similar_videos_ignore_cache(db)
        else:
            return self.find_similar_videos(db)

    def find_similar_videos_ignore_cache(self, db: AbstractDatabase):
        miniatures = db.ensure_miniatures()  # type: List[Miniature]
        video_indices = [m.video_id for m in miniatures]
        previous_sim = [
            row["similarity_id"]
            for row in db.get_videos(
                include=["similarity_id"], where={"video_id": video_indices}
            )
        ]
        db.set_similarities(video_indices, (None for _ in video_indices))
        try:
            self.find_similar_videos(db, miniatures)
        except Exception:
            # Restore previous similarities.
            db.set_similarities(video_indices, previous_sim)
            raise

    def find_similar_videos(
        self, db: AbstractDatabase, miniatures: List[Miniature] = None
    ):
        notifier = Informer.default()
        with Profiler(say("Find similar videos.")), db.to_save():
            if miniatures is None:
                miniatures = db.ensure_miniatures()  # type: List[Miniature]
            video_indices = [m.video_id for m in miniatures]
            prev_sims = [
                row["similarity_id"]
                for row in db.get_videos(
                    include=["similarity_id"], where={"video_id": video_indices}
                )
            ]
            nb_videos = len(miniatures)
            new_miniature_indices = []
            old_miniature_indices = []
            for i, similarity_id in enumerate(prev_sims):
                if similarity_id is None:
                    new_miniature_indices.append(i)
                else:
                    old_miniature_indices.append(i)

            if not new_miniature_indices:
                notifier.notify(notifications.Message(say("No new videos to check.")))
                return

            nb_max_comparisons = compute_nb_couples(nb_videos)
            with Profiler(say("Allocating edges map")):
                cmp_map = self._generate_edges(nb_videos)
            classifier_new = _GrayClassifier.classify(miniatures, new_miniature_indices)
            classifier_old = _GrayClassifier.classify(miniatures, old_miniature_indices)

            nb_cmp = self._collect_comparisons(classifier_new, cmp_map, nb_videos)
            nb_cmp += self._compare_old_vs_new_miniatures(
                classifier_new, classifier_old, cmp_map, nb_videos
            )

            notifier.notify(
                notifications.Message(
                    say(
                        "To do: {count} / {total} comparisons ({percent} %).",
                        count=nb_cmp,
                        total=nb_max_comparisons,
                        percent=(nb_cmp * 100 / nb_max_comparisons),
                    )
                )
            )

            sim_groups = self._find_similar_miniatures(miniatures, cmp_map, db)

            notifier.notify(
                notifications.Message(
                    say(
                        "Finally found {nb_similarities} new similarity groups "
                        "with {nb_images} images.",
                        nb_similarities=len(sim_groups),
                        nb_images=sum(len(g) for g in sim_groups),
                    )
                )
            )
            # Sort new similarity groups by size then smallest duration.
            lengths = [
                row["length"]
                for row in db.get_videos(
                    include=["length"], where={"video_id": video_indices}
                )
            ]
            sim_groups.sort(key=lambda s: (len(s), min(lengths[x] for x in s)))
            # Get next similarity id to use.
            next_sim_id = (
                max((sim_id for sim_id in prev_sims if sim_id is not None), default=0)
                + 1
            )
            with Profiler(say("Merge new similarities with old ones.")):
                sim_id_to_vid_ids = {}
                for i in old_miniature_indices:
                    sim_id_to_vid_ids.setdefault(prev_sims[i], []).append(i)
                sim_id_to_vid_ids.pop(-1, None)
                notifier.notify(
                    notifications.Message(
                        say(
                            "Found {count} old similarities.",
                            count=sum(
                                1 for g in sim_id_to_vid_ids.values() if len(g) > 1
                            ),
                        )
                    )
                )
                graph = Graph()
                for linked_videos in sim_id_to_vid_ids.values():
                    for i in range(1, len(linked_videos)):
                        graph.connect(linked_videos[i - 1], linked_videos[i])
                for linked_videos in sim_groups:
                    linked_videos = list(linked_videos)
                    for i in range(1, len(linked_videos)):
                        graph.connect(linked_videos[i - 1], linked_videos[i])
                new_sim_groups = [
                    group for group in graph.pop_groups() if len(group) > 1
                ]
                notifier.notify(
                    notifications.Message(
                        say(
                            "Found {count} total similarities after merging.",
                            count=len(new_sim_groups),
                        )
                    )
                )
                new_sim_indices = []
                nb_new_indices = 0
                for new_sim_group in new_sim_groups:
                    old_indices = {prev_sims[i] for i in new_sim_group}
                    if -1 in old_indices:
                        old_indices.remove(-1)
                    if None in old_indices:
                        old_indices.remove(None)
                    if not old_indices:
                        new_id = next_sim_id
                        next_sim_id += 1
                        nb_new_indices += 1
                    else:
                        new_id = min(old_indices)
                    new_sim_indices.append(new_id)
                notifier.notify(
                    notifications.Message(
                        say(
                            "Found {count} pure new similarities.", count=nb_new_indices
                        )
                    )
                )

                db.set_similarities(
                    (video_indices[i] for i in new_miniature_indices),
                    (-1 for _ in new_miniature_indices),
                )
                db.set_similarities(
                    [
                        video_indices[i]
                        for new_group in new_sim_groups
                        for i in new_group
                    ],
                    [
                        new_id
                        for (new_id, new_group) in zip(new_sim_indices, new_sim_groups)
                        for _ in new_group
                    ],
                )

    @classmethod
    def _generate_edges(cls, nb_videos):
        if has_cpp:
            return (c_bool * (nb_videos * nb_videos))()
        else:
            return np.zeros(nb_videos * nb_videos, dtype=np.uint32)

    def _collect_comparisons(
        self, classifier: _GrayClassifier, cmp_map: Array, nb_miniatures: int
    ):
        with Profiler(say("Collect comparisons.")):
            nb_cmp = sum(
                compute_nb_couples(len(group))
                for clf in classifier.classifiers
                for group in clf.groups
            )
            for clf in classifier.classifiers:
                for indices in clf.groups:
                    for i, j in itertools.combinations(indices, 2):
                        self._cmp(cmp_map, i * nb_miniatures + j)

            for clf in classifier.classifiers:
                nb_groups = len(clf.groups)
                for i in range(nb_groups):
                    count_i = clf.counts[i]
                    group_i = clf.groups[i]
                    for j in range(i + 1, nb_groups):
                        if abs(count_i - clf.counts[j]) > 40:
                            break
                        group_j = clf.groups[j]
                        nb_cmp += len(group_i) * len(group_j)
                        for a, b in itertools.product(group_i, group_j):
                            if a > b:
                                a, b = b, a
                            self._cmp(cmp_map, a * nb_miniatures + b)

            for r, c in classifier.compare_miniature_grays():
                clr = classifier.classifiers[r]
                clc = classifier.classifiers[c]
                for x_r in range(len(clr.counts)):
                    count_r = clr.counts[x_r]
                    group_r = clr.groups[x_r]
                    for x_c in range(len(clc.counts)):
                        if abs(count_r - clc.counts[x_c]) > 40:
                            break
                        group_c = clc.groups[x_c]
                        nb_cmp += len(group_r) * len(group_c)
                        for i, j in itertools.product(group_r, group_c):
                            if i > j:
                                i, j = j, i
                            self._cmp(cmp_map, i * nb_miniatures + j)

            return nb_cmp

    def _compare_old_vs_new_miniatures(
        self,
        classifier_left: _GrayClassifier,
        classifier_right: _GrayClassifier,
        cmp_map: Array,
        nb_miniatures: int,
    ):
        notifier = Informer.default()
        n = len(classifier_left.grays)
        with Profiler(say("Cross compare classifiers.")):
            notifier.task(self._compare_old_vs_new_miniatures, n, "new miniatures")
            nb_cmp = 0
            for i_gray_left, gray_left in enumerate(classifier_left.grays):
                sub_classifier_left = classifier_left.classifiers[i_gray_left]
                i_start_gray_right = get_start_index(
                    classifier_right.grays, gray_left - GRAY_DEC
                )
                i_end_gray_right = get_end_index(
                    classifier_right.grays, gray_left + GRAY_DEC
                )
                for i_gray_right in range(i_start_gray_right, i_end_gray_right):
                    sub_classifier_right = classifier_right.classifiers[i_gray_right]
                    for i_count_left, count_left in enumerate(
                        sub_classifier_left.counts
                    ):
                        group_left = sub_classifier_left.groups[i_count_left]
                        i_start_count_right = get_start_index(
                            sub_classifier_right.counts, count_left - 40
                        )
                        i_end_count_right = get_end_index(
                            sub_classifier_right.counts, count_left + 40
                        )
                        for i_count_right in range(
                            i_start_count_right, i_end_count_right
                        ):
                            group_right = sub_classifier_right.groups[i_count_right]
                            nb_cmp += len(group_left) * len(group_right)
                            for a, b in itertools.product(group_left, group_right):
                                if a > b:
                                    a, b = b, a
                                self._cmp(cmp_map, a * nb_miniatures + b)
                if (i_gray_left + 1) % 10 == 0:
                    notifier.progress(
                        self._compare_old_vs_new_miniatures, i_gray_left + 1, n
                    )
            notifier.progress(self._compare_old_vs_new_miniatures, n, n)
            return nb_cmp

    def _cmp(self, cmp_map: Array, pos: int):
        cmp_map[pos] = 1
        # TODO Discard positions if too long, as it won't be so much faster (?)
        if self.positions is not None:
            if len(self.positions) < 1_000_000:
                self.positions.append(pos)
            else:
                self.positions = None

    def _find_similar_miniatures(self, miniatures, edges, db):
        # type: (List[Miniature], Array[c_bool], AbstractDatabase) -> List[Set[int]]
        notifier = Informer.default()
        backend_sim.classify_similarities_directed(miniatures, edges, SIM_LIMIT)
        graph = Graph()
        nb_miniatures = len(miniatures)
        with Profiler(say("Link videos ...")):
            if self.positions:
                nb_pos = len(self.positions)
                notifier.task("link_compared_miniatures", nb_pos, "positions")
                for index, pos in enumerate(self.positions):
                    if edges[pos]:
                        graph.connect(pos // nb_miniatures, pos % nb_miniatures)
                    if (index + 1) % 500 == 0:
                        notifier.progress("link_compared_miniatures", index + 1, nb_pos)
                notifier.progress("link_compared_miniatures", nb_pos, nb_pos)
                self.positions.clear()
            else:
                notifier.task("link_compared_videos", nb_miniatures, "videos")
                for i in range(nb_miniatures):
                    for j in range(i + 1, nb_miniatures):
                        if edges[i * nb_miniatures + j]:
                            graph.connect(i, j)
                    if (i + 1) % 500 == 0:
                        notifier.progress("link_compared_videos", i + 1, nb_miniatures)
                notifier.progress("link_compared_videos", nb_miniatures, nb_miniatures)
        return [group for group in graph.pop_groups() if len(group) > 1]
