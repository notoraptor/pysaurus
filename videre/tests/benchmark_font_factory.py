import functools
import sys

from tqdm import trange

from pysaurus.core.components import Duration
from pysaurus.core.constants import LOREM_IPSUM
from pysaurus.core.profiling import PerfCounter
from resource.fonts import FONT_NOTO_REGULAR
from videre import Colors, Gradient
from videre.utils.pygame_font_factory import PygameFontFactory


def benchmark(batch=200):
    height_delta = 2
    ff = PygameFontFactory(size=24, overrides=[FONT_NOTO_REGULAR.path])
    line_height = ff.get_font(" ").get_sized_height(ff.size) + height_delta
    assert line_height == 35

    text = LOREM_IPSUM
    print("Text length:", len(text), file=sys.stderr)

    ff_render_text = functools.partial(ff.render_text, width=None, compact=True)
    with PerfCounter() as pc:
        for _ in trange(batch):
            ff_render_text(text)
    print(
        "Time:",
        Duration(pc.nanoseconds / 1000),
        "Unit:",
        Duration(pc.nanoseconds / 1000 / batch),
        file=sys.stderr,
    )


def benchmark_gradient(batch=200):
    grad = Gradient(Colors.white, Colors.green, Colors.blue, Colors.yellow)
    for _ in trange(batch):
        grad.generate(3840, 2160)


if __name__ == "__main__":
    benchmark()
