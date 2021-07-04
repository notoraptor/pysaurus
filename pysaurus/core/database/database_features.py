import itertools
from ctypes import Array, c_bool
from typing import List, Set

from pysaurus.core import notifications
from pysaurus.core.database.database import Database
from pysaurus.core.database.video import Video
from pysaurus.core.fraction import Fraction
from pysaurus.core.functions import compute_nb_couples, get_start_index, get_end_index
from pysaurus.core.miniature_tools.graph import Graph
from pysaurus.core.miniature_tools.miniature import Miniature
from pysaurus.core.native.alignment_raptor import alignment as native_alignment
from pysaurus.core.notifier import Notifier
from pysaurus.core.profiling import Profiler
from pysaurus.core.testing import TEST_LIST_FILE_PATH

FRAC_SIM_LIMIT = Fraction(90, 100)
FRAC_DST_LIMIT = Fraction(1) - FRAC_SIM_LIMIT
SIM_LIMIT = float(FRAC_SIM_LIMIT)
DST_LIMIT = float(FRAC_DST_LIMIT)
GRAY_DEC = float(Fraction(255) * FRAC_DST_LIMIT)


class NbGroupsClassifier:
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


class GrayClassifier:
    __slots__ = "grays", "classifiers", "j_limit"

    def __init__(self, grays: List[float], classifiers: List[NbGroupsClassifier]):
        self.grays = grays
        self.classifiers = classifiers
        self.j_limit = [
            get_end_index(grays, grays[i] + GRAY_DEC, i + 1) for i in range(len(grays))
        ]

    def cross_comparisons(self, notifier: Notifier):
        """Return sequence of couples of indices of classifiers to cross compare."""
        n = len(self.grays)
        t = self.j_limit
        for i in range(n):
            for j in range(i + 1, t[i]):
                yield i, j
            if (i + 1) % 1000 == 0:
                notifier.notify(notifications.GrayCrossComparisonJob(None, i + 1, n))
        notifier.notify(notifications.GrayCrossComparisonJob(None, n, n))

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
            gray: NbGroupsClassifier.classify(miniatures, indices)
            for gray, indices in gray_to_identifiers.items()
        }
        gray_then_classifier = sorted(
            gray_to_classifier.items(), key=lambda item: item[0]
        )
        return cls(
            [float(gray) for gray, _ in gray_then_classifier],
            [classifier for _, classifier in gray_then_classifier],
        )


class DatabaseFeatures:
    @classmethod
    def _collect_comparisons(
        cls,
        classifier: GrayClassifier,
        cmp_map: Array,
        nb_miniatures: int,
        notifier: Notifier,
    ):
        with Profiler("Collect comparisons."):
            nb_cmp = sum(
                compute_nb_couples(len(group))
                for clf in classifier.classifiers
                for group in clf.groups
            )
            for clf in classifier.classifiers:
                for indices in clf.groups:
                    for i, j in itertools.combinations(indices, 2):
                        cmp_map[i * nb_miniatures + j] = 1

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
                            cmp_map[a * nb_miniatures + b] = 1

            for r, c in classifier.cross_comparisons(notifier):
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
                            cmp_map[i * nb_miniatures + j] = 1

            return nb_cmp

    @classmethod
    def _cross_compare_classifiers(
        cls,
        classifier_left: GrayClassifier,
        classifier_right: GrayClassifier,
        cmp_map: Array,
        nb_miniatures: int,
        notifier: Notifier,
    ):
        with Profiler("Cross compare classifiers."):
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
                            sub_classifier_right.counts,
                            count_left + 40,
                        )
                        for i_count_right in range(
                            i_start_count_right, i_end_count_right
                        ):
                            group_right = sub_classifier_right.groups[i_count_right]
                            nb_cmp += len(group_left) * len(group_right)
                            for a, b in itertools.product(group_left, group_right):
                                if a > b:
                                    a, b = b, a
                                cmp_map[a * nb_miniatures + b] = 1
                if (i_gray_left + 1) % 10 == 0:
                    notifier.notify(
                        notifications.NewCrossComparisonJob(
                            None, i_gray_left + 1, len(classifier_left.grays)
                        )
                    )
            notifier.notify(
                notifications.NewCrossComparisonJob(
                    None, len(classifier_left.grays), len(classifier_left.grays)
                )
            )
            return nb_cmp

    @classmethod
    def _find_similar_miniatures(cls, miniatures, edges):
        # type: (List[Miniature], Array[c_bool]) -> List[Set[int]]
        native_alignment.classify_similarities_directed(miniatures, edges, SIM_LIMIT)
        graph = Graph()
        nb_miniatures = len(miniatures)
        for i in range(len(miniatures)):
            for j in range(i + 1, len(miniatures)):
                if edges[i * nb_miniatures + j]:
                    graph.connect(i, j)
        return [group for group in graph.pop_groups() if len(group) > 1]

    @classmethod
    def find_similar_videos(cls, db: Database):
        videos = db.ensure_miniatures(returns=True)  # type: List[Video]
        nb_videos = len(videos)
        miniatures = []
        new_miniature_indices = []
        old_miniature_indices = []
        for i, video in enumerate(videos):
            miniatures.append(video.miniature)
            if video.similarity_id is None:
                new_miniature_indices.append(i)
            else:
                old_miniature_indices.append(i)

        if new_miniature_indices:
            nb_max_comparisons = compute_nb_couples(nb_videos)
            cmp_map = (c_bool * (nb_videos * nb_videos))()
            classifier_new = GrayClassifier.classify(miniatures, new_miniature_indices)
            classifier_old = GrayClassifier.classify(miniatures, old_miniature_indices)

            nb_cmp = cls._collect_comparisons(
                classifier_new, cmp_map, nb_videos, db.notifier
            )
            nb_cmp += cls._cross_compare_classifiers(
                classifier_new, classifier_old, cmp_map, nb_videos, db.notifier
            )

            db.notifier.notify(
                notifications.Message(
                    f"To do: {nb_cmp} / {nb_max_comparisons} comparisons "
                    f"({nb_cmp * 100 / nb_max_comparisons} %)."
                )
            )

            sim_groups = cls._find_similar_miniatures(miniatures, cmp_map)

            db.notifier.notify(
                notifications.Message(
                    f"Finally found {len(sim_groups)} new similarity groups "
                    f"with {sum(len(g) for g in sim_groups)} images."
                )
            )

            for i in new_miniature_indices:
                videos[i].similarity_id = -1
            sim_groups.sort(key=lambda s: (len(s), min(videos[i].length for i in s)))
            next_sim_id = (
                max(v.similarity_id for v in videos if v.similarity_id is not None) + 1
            )
            for indices in sim_groups:
                new_sim_id = next_sim_id
                next_sim_id += 1
                for i in indices:
                    videos[i].similarity_id = new_sim_id
            db.save()
        else:
            sim_groups = {}
            for video in videos:
                if video.similarity_id is not None and video.similarity_id > -1:
                    sim_groups.setdefault(video.similarity_id, []).append(video)
            db.notifier.notify(notifications.Message(f"No new videos to check."))


@Profiler.profile()
def main():
    db = Database.load_from_list_file_path(
        TEST_LIST_FILE_PATH, update=True, ensure_miniatures=False
    )
    DatabaseFeatures.find_similar_videos(db)


if __name__ == "__main__":
    main()
