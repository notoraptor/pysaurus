import json
import sys

from pysaurus.core.components import AbsolutePath
from pysaurus.core.profiling import InlineProfiler, Profiler


class Checker:
    __slots__ = ("video_to_sim", "sim_groups", "ways")

    def __init__(self, ways):
        with InlineProfiler("Get pre-computed similarities"):
            with open(ways.db_json_path.path) as json_file:
                content = json.load(json_file)
            groups = {}
            for video in content.get("videos", ()):
                groups.setdefault(video.get("S", None), []).append(
                    AbsolutePath(video["f"]).path
                )
            groups.pop(-1, None)
            groups.pop(None, None)
            sim_groups = sorted(
                (
                    (value, sorted(videos))
                    for value, videos in groups.items()
                    if len(videos) > 1
                ),
                key=lambda c: c[0],
            )
            video_to_sim = {
                filename: value
                for value, filenames in sim_groups
                for filename in filenames
            }

        self.ways = ways
        self.video_to_sim = video_to_sim
        self.sim_groups = sim_groups

    def save(self, output, metric):
        with open(f"ignored/results_{metric}_dict.json", "w") as file:
            json.dump(output, file, indent=1)

    def check(self, output, new_sim_groups):
        video_to_sim = self.video_to_sim
        sim_groups = self.sim_groups

        print(
            "Comparisons to do", sum(len(d) for d in output.values()), file=sys.stderr
        )

        nb_similar_videos = sum(len(videos) for _, videos in sim_groups)
        print("Similarities", len(sim_groups), file=sys.stderr)
        print("Similar videos", nb_similar_videos, file=sys.stderr)
        if new_sim_groups:
            nb_new_similar_videos = sum(len(group) for group in new_sim_groups)
            nb_new_similar_groups = len(new_sim_groups)
            print("New similarities", nb_new_similar_groups, file=sys.stderr)
            print("New similar videos", nb_new_similar_videos, file=sys.stderr)

        with InlineProfiler("Check new sim groups"):
            for group in new_sim_groups:
                old_sims = {video_to_sim.get(filename, -1) for filename in group}
                if len(old_sims) != 1:
                    print("Bad group", file=sys.stderr)
                    for filename in group:
                        print(
                            "\t",
                            video_to_sim.get(filename, -1),
                            filename,
                            file=sys.stderr,
                        )
                else:
                    (sim,) = list(old_sims)
                    if sim == -1:
                        print("New group", file=sys.stderr)
                        for filename in group:
                            print("\t", filename, file=sys.stderr)

        with Profiler("Check expected similarities"):
            for sim_id, videos in sim_groups:
                missing_is_printed = False
                filename, *linked_filenames = videos
                for linked_filename in linked_filenames:
                    has_l = filename in output and linked_filename in output[filename]
                    has_r = (
                        linked_filename in output
                        and filename in output[linked_filename]
                    )
                    if not has_l and not has_r:
                        if not missing_is_printed:
                            print("Missing", sim_id, file=sys.stderr)
                            print("\t*", filename, file=sys.stderr)
                            missing_is_printed = True
                        print("\t ", linked_filename, file=sys.stderr)
