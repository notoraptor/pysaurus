import functools
import sys

from tqdm import trange

from pysaurus.core.components import Duration
from pysaurus.core.constants import LOREM_IPSUM
from pysaurus.core.perf_counter import PerfCounter
from videre import Colors, Gradient
from videre.core.fontfactory.pygame_font_factory import PygameFontFactory


def stress_render_text(batch=200):
    height_delta = 2
    ff = PygameFontFactory(size=24)
    line_height = ff.standard_size + height_delta
    assert line_height == 35

    text = LOREM_IPSUM
    print("Text length:", len(text), file=sys.stderr)

    ff_render_text = functools.partial(ff.render_text, width=None, compact=True)

    for _ in trange(batch):
        ff_render_text(text)


def stress_gradient(batch=200):
    grad = Gradient(Colors.white, Colors.green, Colors.blue, Colors.yellow)
    for _ in trange(batch):
        grad.generate(3840, 2160)


def benchmark(function):
    print(f"[benchmark/{function.__name__}]", file=sys.stderr)
    batch = 200
    with PerfCounter() as pc:
        function(batch)
    print(
        "Time:",
        Duration(pc.nanoseconds / 1000),
        "Unit:",
        Duration(pc.nanoseconds / 1000 / batch),
        file=sys.stderr,
    )


if __name__ == "__main__":
    benchmark(stress_render_text)
    benchmark(stress_gradient)
