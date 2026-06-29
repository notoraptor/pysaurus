"""Videroid FIRST-render phase breakdown across page sizes (low-overhead timers).

Splits the first render into shape / paint / raster / other via 2 timestamps per
wrapped seam (negligible vs HarfBuzz), median of COLD_REPS cold cycles per size:
  first  = whole win.render() wall time          (the only RELIABLE number)
  shape  = Text.(get_)document  (partition + HarfBuzz, cached after)
  paint  = Text.draw - shape    (layout + glyph raster + Drawer build)
  raster = render_drawer        (pixel compositing of visible cards; GPU-able)
  other  = first - raster - Text.draw

WARNING: the shape/paint split is NOISY at this granularity (medians don't sum;
swings ~40% run-to-run). Use it only as a rough where-does-time-go map; to decide
whether a change actually helps, use bench_first_500.py and compare TOTALS over
many cold cycles. raster being ~0.2% confirms a GPU backend won't speed up text.

Requires the local "Divertissement" DB. videre is an editable dep of pysaurus,
so videre working-tree changes are live; stash/unstash between before/after runs
in the same session.

Run (from the pysaurus project root):
    uv run python wip/videroid_perf/bench_phases.py
"""

import statistics
import sys
import time
from collections import defaultdict

from videre.core.pygame_backend.backend import PygameRenderer
from videre.testing.step_window import StepWindow
from videre.widgets.text import Text

from pysaurus.core.informer import Information
from pysaurus.interface.videroid.app import VideroidApp

DB = sys.argv[1] if len(sys.argv) > 1 else "Divertissement"
SIZES = [100, 300, 500]
COLD_REPS = 3

stats = defaultdict(lambda: [0, 0.0])


def wrap(cls, meth, label):
    orig = getattr(cls, meth)

    def wrapper(*a, **k):
        t0 = time.perf_counter()
        try:
            return orig(*a, **k)
        finally:
            s = stats[label]
            s[0] += 1
            s[1] += time.perf_counter() - t0

    setattr(cls, meth, wrapper)


# The shape seam was Text._get_document, renamed to public get_document
# (2026-06-26); support both so this bench survives either videre revision.
SHAPE_METH = "get_document" if hasattr(Text, "get_document") else "_get_document"
wrap(Text, "draw", "text_draw")
wrap(Text, SHAPE_METH, "shape")
wrap(PygameRenderer, "render_drawer", "raster")


def main() -> None:
    with Information():
        with StepWindow(width=1280, height=900) as win:
            app = VideroidApp(window=win)
            try:
                api = app.context._api
                api.database = api.application.open_database_from_name(DB, False)
                app.show_page("videos")
                win.render()
                vp = app._pages["videos"]

                print(
                    f"shape seam = Text.{SHAPE_METH}, median of {COLD_REPS} cold cycles\n"
                )
                print(
                    f"{'cards':>6} {'first ms':>9} {'shape ms':>9} {'paint ms':>9} "
                    f"{'raster ms':>10} {'other ms':>9}"
                )
                print("-" * 56)
                for size in SIZES:
                    firsts, shapes, paints, rasters, others = [], [], [], [], []
                    n = 0
                    for _ in range(COLD_REPS):
                        vp.page_size = size  # setter resets page + reloads (cold rebuild)
                        stats.clear()
                        t0 = time.perf_counter()
                        win.render()
                        total = time.perf_counter() - t0
                        n = len(vp._cards.controls)
                        shape = stats["shape"][1]
                        text_draw = stats["text_draw"][1]
                        raster = stats["raster"][1]
                        firsts.append(total * 1000)
                        shapes.append(shape * 1000)
                        paints.append((text_draw - shape) * 1000)
                        rasters.append(raster * 1000)
                        others.append((total - raster - text_draw) * 1000)
                    m = statistics.median
                    print(
                        f"{n:>6} {m(firsts):>9.0f} {m(shapes):>9.0f} {m(paints):>9.0f} "
                        f"{m(rasters):>10.1f} {m(others):>9.0f}"
                    )
            finally:
                app.context.close_app()


if __name__ == "__main__":
    main()
