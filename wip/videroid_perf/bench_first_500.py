"""Videroid FIRST-render TOTAL, focused: one page size, many cold cycles.

Reports ONLY the first-render wall time distribution (min / median / max) over
COLD_REPS cold cycles. The page-level shape/paint phase split is bucket-
attribution NOISE (medians don't sum; a single run once showed paint -44% while
the total went +5.6%), so do NOT trust it -- trust only this total, over many
cycles, comparing non-overlapping before/after distributions.

Requires the local "Divertissement" DB (a real DB on this machine, not a test
fixture). videre is an editable dependency of pysaurus, so videre working-tree
changes are picked up live -- stash/unstash videre between before/after runs in
the SAME session (same machine state) to compare.

Run (from the pysaurus project root):
    uv run python wip/videroid_perf/bench_first_500.py
    uv run python wip/videroid_perf/bench_first_500.py Divertissement 500 6
"""

import statistics
import sys
import time

from videre.testing.step_window import StepWindow

from pysaurus.core.informer import Information
from pysaurus.interface.videroid.app import VideroidApp

DB = sys.argv[1] if len(sys.argv) > 1 else "Divertissement"
SIZE = int(sys.argv[2]) if len(sys.argv) > 2 else 500
COLD_REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 6


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

                firsts = []
                n = 0
                for _ in range(COLD_REPS):
                    vp.page_size = (
                        SIZE  # setter rebuilds widgets -> cold per-widget docs
                    )
                    t0 = time.perf_counter()
                    win.render()  # FIRST render of `SIZE` cards
                    firsts.append((time.perf_counter() - t0) * 1000)
                    n = len(vp._cards.controls)

                ordered = sorted(firsts)
                print(f"\n{n} cards, first render (ms), {COLD_REPS} cold cycles:")
                print("  all   :", " ".join(f"{x:.0f}" for x in firsts))
                print(f"  min   : {ordered[0]:.0f}")
                print(f"  median: {statistics.median(firsts):.0f}")
                print(f"  max   : {ordered[-1]:.0f}")
            finally:
                app.context.close_app()


if __name__ == "__main__":
    main()
