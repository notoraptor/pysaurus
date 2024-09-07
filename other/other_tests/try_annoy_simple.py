from other.imgsimsearchother.utils import compare_images_native
from other.other_tests.local_image_provider import LocalImageProvider, save_similarities
from pysaurus.core.informer import Informer
from pysaurus.core.profiling import Profiler
from pysaurus.imgsimsearch.approximate_comparator_annoy import (
    ApproximateComparatorAnnoy,
)


def main_functional():
    imp = LocalImageProvider()
    ac = ApproximateComparatorAnnoy(imp)
    combined = ac.get_comparable_images_cos()
    similarities = compare_images_native(imp, combined)
    save_similarities(imp.ways.db_json_path, similarities)


def main():
    with Informer.default():
        with Profiler("main"):
            main_functional()


if __name__ == "__main__":
    main()
