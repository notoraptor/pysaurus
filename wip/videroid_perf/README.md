# videroid perf benchmarks

Measure videre's text-rendering performance **through videroid** (the real
GUI under `pysaurus/interface/videroid/`) on a real database. Used to find and
verify videre-level perf changes at scale (a page of many video cards).

## Setup (two repos, one editable link)

- videre lives at `../videre` and is an **editable** dependency of pysaurus
  (`pyproject.toml`: `videre = { path = "../videre", editable = true }`).
- So **videre working-tree changes are picked up live** here — no reinstall.
- To A/B a videre change: in the videre repo, `git stash` it, run a bench here
  (BEFORE), `git stash pop`, run again (AFTER) — **same session, same machine
  state** (these numbers drift a lot run-to-run).

## Requirements

- The local **"Divertissement"** database (a real DB on this machine, not a
  test fixture). Pass another DB name as the first CLI arg if needed.

## Scripts

```bash
# From the pysaurus project root:

# First-render TOTAL at 500 cards, 6 cold cycles -> min/median/max.
# THE decision tool: compare totals before/after a videre change.
uv run python wip/videroid_perf/bench_first_500.py
uv run python wip/videroid_perf/bench_first_500.py Divertissement 500 6

# Phase breakdown (shape/paint/raster/other) across 100/300/500 cards.
# A rough where-does-time-go map only -- the split is noisy, see below.
uv run python wip/videroid_perf/bench_phases.py
```

If your shell isn't in the pysaurus dir, use
`uv run --project C:/data/git/pysaurus python <script>`.

## Methodology (learned the hard way)

- **Trust only the `first` TOTAL, over many cold cycles.** The page-level
  shape/paint phase split is bucket-attribution noise: medians don't sum, and a
  single run once showed paint −44% while the total went +5.6% (a fluke). It
  took 6 cold cycles to see the real ~−5.5% total. Use `bench_first_500.py` and
  compare **non-overlapping** before/after distributions.
- **cProfile is useless here** — it adds 4×+ on HarfBuzz C code and distorts the
  picture. These scripts use lightweight `perf_counter` seams instead.
- The first render is ~72% **shape** (HarfBuzz + Unicode segmentation, all CPU)
  and ~0.2% **raster** — so a GPU backend would NOT speed up text. The only
  order-of-magnitude lever left is virtualizing the *build* (don't shape
  off-screen cards); paint/shape micro-opts cap out around −15% combined.

## See also

- `../videre/tools/bench_text.py` — isolated shape vs paint micro-bench on text
  samples (no videroid). Cleaner for measuring the paint or shape phase alone,
  since it doesn't mix in the noisy page-level total.
