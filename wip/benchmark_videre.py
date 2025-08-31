import sys

from tqdm import trange
from videre import Colors, Gradient
from videre.core.fontfactory.pygame_font_factory import PygameFontFactory
from videre.core.fontfactory.pygame_text_rendering import PygameTextRendering
from videre.testing.utils import LOREM_IPSUM

from pysaurus.core.components import Duration
from pysaurus.core.perf_counter import PerfCounter


def stress_render_text(batch=200):
    height_delta = 2
    ff = PygameFontFactory(size=24)
    tr = PygameTextRendering(ff, height_delta=height_delta)

    line_height = ff.font_height + height_delta
    assert line_height == 35

    text = LOREM_IPSUM
    print("Text length:", len(text), file=sys.stderr)

    for _ in trange(batch):
        tr.render_text(text, None)


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
        Duration(pc.microseconds),
        "Unit:",
        Duration(pc.microseconds / batch),
        file=sys.stderr,
    )


if __name__ == "__main__":
    benchmark(stress_render_text)
    benchmark(stress_gradient)
