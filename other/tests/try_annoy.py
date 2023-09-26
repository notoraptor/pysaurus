"""
Distance angular: 1.4142135381698608
Distance euclidean: 14133.435546875
sqrt 55.42523743872549 sqrt^2 3071.9569451390976
Distance manhattan: 783360.0
Distance hamming: 3072.0
Distance dot: 0.0
Expected euclidian 14133.534589762037 55.42562584220407
Expected manhattan 783360
========================================================================================
ProfilingStart(main)
ProfilingStart(Get pre-computed similarities)
ProfilingEnded(Get pre-computed similarities, 552830µs)
Similarities 79
Similar videos 159
get vectors: 100%|██████████| 25247/25247 [00:20<00:00, 1209.56it/s]
check vectors: 100%|██████████| 25247/25247 [00:00<00:00, 2945825.61it/s]
Add items to Annoy: 100%|██████████| 25247/25247 [00:03<00:00, 8004.22it/s]
ProfilingStart(Build Annoy trees)
ProfilingEnded(Build Annoy trees, 09s 081409µs)
ProfilingStart(Save Annoy to disk)
ProfilingEnded(Save Annoy to disk, 414209µs)
Search in Annoy index: 100%|██████████| 25247/25247 [04:11<00:00, 100.20it/s]
Expected sims 159
Detected sims 435493
Truth rate 0.03651034574608547 %
ProfilingStart(Check expected similarities)
ProfilingEnded(Check expected similarities, 000133µs)
ProfilingEnded(main, 04m 48s 981723µs)
"""

from imgsimsearch.approximate_comparator import ApproximateComparator
from imgsimsearch.native_fine_comparator import compare_images_native
from other.tests.similarity_checker import Checker
from other.tests.utils_testing import LocalImageProvider
from pysaurus.core.profiling import Profiler


def main_new():
    imp = LocalImageProvider()
    chk = Checker(imp.ways)
    ac = ApproximateComparator(imp)

    output_angular = ac.get_comparable_images_cos()
    chk.check(output_angular, [])

    output_euclidian = ac.get_comparable_images_euc()
    chk.check(output_euclidian, [])

    all_filenames = sorted(set(output_angular) | set(output_euclidian))
    combined = {
        filename: sorted(
            set(output_angular.get(filename, ()))
            & set(output_euclidian.get(filename, ()))
        )
        for filename in all_filenames
    }
    chk.check(combined, [])

    final_output = {}
    similarities = compare_images_native(imp, combined)
    for group in similarities:
        group = list(group)
        final_output[group[0]] = set(group[1:])
    chk.check(final_output, similarities)


if __name__ == "__main__":
    with Profiler("main"):
        main_new()
