from imgsimsearch.abstract_image_provider import AbstractImageProvider
from imgsimsearch.approximate_comparator import ApproximateComparator
from imgsimsearch.native_fine_comparator import compare_images_native


def search_similar_images(imp: AbstractImageProvider):
    ac = ApproximateComparator(imp)

    approx_cos = ac.get_comparable_images_cos()
    approx_euc = ac.get_comparable_images_euc()

    all_filenames = sorted(set(approx_cos) | set(approx_euc))
    approx_combined = {
        filename: sorted(
            set(approx_cos.get(filename, ())) & set(approx_euc.get(filename, ()))
        )
        for filename in all_filenames
    }

    return compare_images_native(imp, approx_combined)
