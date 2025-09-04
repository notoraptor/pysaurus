import json
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import matplotlib.pyplot as plt


class BenchmarkDict(TypedDict):
    microseconds: float
    timestamp: float


class Benchline:
    def __init__(self, title: str = "", folder: str = ".", reset=False):
        title = title or ".benchmark"
        folder = Path(folder).resolve()
        bench_path = folder / f"{title}.json"
        plot_path = folder / f"{title}.jpg"
        self.title = title
        self.bench_path = bench_path
        self.plot_path = plot_path
        self.benchmarks: list[BenchmarkDict] = []
        if not reset:
            self._load()

    def add(self, microseconds: float, timestamp: datetime | float | None = None):
        if timestamp is None:
            timestamp = datetime.now()
        if isinstance(timestamp, datetime):
            timestamp = timestamp.timestamp()
        else:
            assert isinstance(timestamp, float)

        assert not self.benchmarks or self.benchmarks[-1]["timestamp"] < timestamp

        self.benchmarks.append(
            BenchmarkDict(microseconds=microseconds, timestamp=timestamp)
        )
        self._save()

    def _load(self):
        if self.bench_path.exists():
            assert self.bench_path.is_file()
            with open(self.bench_path, mode="r", encoding="utf-8") as f:
                self.benchmarks = json.load(f)

    def _save(self):
        with open(self.bench_path, mode="w", encoding="utf-8") as f:
            json.dump(self.benchmarks, f, indent=1)

    def plot(self, show: bool = False):
        if not self.benchmarks:
            return

        dates = [record["timestamp"] for record in self.benchmarks]
        durations = [record["microseconds"] for record in self.benchmarks]

        fig, ax = plt.subplots()
        ax.plot(dates, durations, marker="o", linestyle="-")
        plt.title(self.title)
        plt.xlabel("Timestamp (sec)")
        plt.ylabel("Duration (μ•sec)")
        plt.savefig(self.plot_path)
        if show:
            plt.show()
        plt.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.plot()


if __name__ == "__main__":
    with Benchline(reset=True) as line:
        line.add(12)
        line.add(11)
        line.add(12)
        line.add(10)
        line.add(9)
        line.add(8)
        line.add(7)
        line.add(6)
        line.add(5)
        line.add(2)
        line.add(11)
