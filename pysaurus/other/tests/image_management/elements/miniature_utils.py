from pysaurus.core.fraction import Fraction
from pysaurus.core.miniature import Miniature


def global_intensity(miniature):
    # type: (Miniature) -> Fraction
    return Fraction(
        sum(miniature.r) + sum(miniature.g) + sum(miniature.b), 3 * miniature.size
    )
