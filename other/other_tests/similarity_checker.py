import json
from typing import Dict, List, Tuple

from pysaurus.core.components import AbsolutePath
from pysaurus.core.profiling import Profiler


class Checker:
    __slots__ = ("video_to_sim", "sim_groups", "ways")

    def __init__(self, ways):
        with Profiler("Get pre-computed similarities"):
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
        self.video_to_sim: Dict[str, int] = video_to_sim
        self.sim_groups: List[Tuple[int, List[str]]] = sim_groups

    @classmethod
    def save(cls, output, metric):
        with open(f"ignored/results_{metric}_dict.json", "w") as file:
            json.dump(output, file, indent=1)

    def check(self, output, new_sim_groups):
        video_to_sim = self.video_to_sim
        sim_groups = self.sim_groups

        print("Comparisons to do", sum(len(d) for d in output.values()))

        nb_similar_videos = sum(len(videos) for _, videos in sim_groups)
        print("Similarities", len(sim_groups))
        print("Similar videos", nb_similar_videos)
        if new_sim_groups:
            nb_new_similar_videos = sum(len(group) for group in new_sim_groups)
            nb_new_similar_groups = len(new_sim_groups)
            print("New similarities", nb_new_similar_groups)
            print("New similar videos", nb_new_similar_videos)

        with Profiler("Check new sim groups"):
            for group in new_sim_groups:
                old_sims = {video_to_sim.get(filename, -1) for filename in group}
                if len(old_sims) != 1:
                    print("Bad group")
                    for filename in group:
                        print("\t", video_to_sim.get(filename, -1), filename)
                else:
                    (sim,) = list(old_sims)
                    if sim == -1:
                        print("New group")
                        for filename in group:
                            print("\t", filename)

        seen = set()
        with Profiler("Check expected similarities"):
            for sim_id, videos in sim_groups:
                filename, *linked_filenames = videos
                for linked_filename in linked_filenames:
                    key = (
                        (linked_filename, filename)
                        if filename > linked_filename
                        else (filename, linked_filename)
                    )
                    if key in seen:
                        continue
                    seen.add(key)

                    has_l = filename in output and linked_filename in output[filename]
                    has_r = (
                        linked_filename in output
                        and filename in output[linked_filename]
                    )

                    if not has_l and not has_r:
                        print("Missing", sim_id)
                        print("\t*", filename)
                        print("\t ", linked_filename)
