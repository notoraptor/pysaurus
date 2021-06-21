from typing import List
import ujson as json

from pysaurus.core.components import AbsolutePath
from pysaurus.core.database.database import Database
from pysaurus.core.database.properties import PropType
from pysaurus.core.miniature import Miniature
from pysaurus.core.profiling import Profiler
from pysaurus.core.testing import TEST_LIST_FILE_PATH
from pysaurus.other.tests.image_management.elements.decomposed_miniature import (
    DecomposedMiniature,
)
from pysaurus.other.tests.image_management.elements.group_computer import GroupComputer
from pysaurus.other.tests.image_management.elements.spaced_points import (
    SpacedPoints,
    SpacedPoints32To64,
)


def load_default_database() -> Database:
    return Database.load_from_list_file_path(
        TEST_LIST_FILE_PATH, update=False, ensure_miniatures=False
    )


def _print_stats(dec_mins: List[DecomposedMiniature]):
    nb_min_groups = min(len(dm.pixel_groups) for dm in dec_mins)
    nb_max_groups = max(len(dm.pixel_groups) for dm in dec_mins)
    nb_min_size = min(len(g.members) for dm in dec_mins for g in dm.pixel_groups)
    nb_max_size = max(len(g.members) for dm in dec_mins for g in dm.pixel_groups)
    print("Nb  groups from", nb_min_groups, "to", nb_max_groups)
    print("Group size from", nb_min_size, "to", nb_max_size)


def average_pixel(pixels):
    nb_pixels = len(pixels)
    sum_r = 0
    sum_g = 0
    sum_b = 0
    for r, g, b in pixels:
        sum_r += r
        sum_g += g
        sum_b += b
    return sum_r / nb_pixels, sum_g / nb_pixels, sum_b / nb_pixels


def quad_sign(m: Miniature, spaced_color: SpacedPoints):
    z_tr = []
    z_tl = []
    z_br = []
    z_bl = []
    t = list(m.data())
    half_len = len(t) // 2
    width = m.width
    for y in range(0, m.height // 2):
        z_tl += t[(y * width) : (y * width + width // 2)]
        z_tr += t[(y * width + width // 2) : ((y + 1) * width)]
        z_bl += t[(half_len + y * width) : (half_len + y * width + width // 2)]
        z_br += t[(half_len + y * width + width // 2) : (half_len + (y + 1) * width)]
    return tuple(
        spaced_color.nearest_point(sum(average_pixel(zone)) / 3)
        for zone in (z_tl, z_tr, z_bl, z_br)
    )


class RawSim:
    def __init__(self, group_to_paths: List[List[str]]):
        self.group_to_paths = group_to_paths
        self.path_to_group = {
            p: i
            for i, ps in enumerate(self.group_to_paths)
            for p in ps
        }

    def __bool__(self):
        return bool(self.group_to_paths)

    def get_groups(self, paths):
        group_to_paths = {}
        for p in paths:
            group_to_paths.setdefault(self.path_to_group.get(p, -1), []).append(p)
        return [
            sub_paths
            for group_id, sub_paths in group_to_paths.items()
            if group_id > -1 and len(sub_paths) > 1
        ]


def get_raw_similarities(path=None):
    path = AbsolutePath.ensure(path or r"C:\data\git\.local\.html\similarities.json")
    if path.isfile():
        with open(path.path) as file:
            return RawSim(json.load(file))
    return None


@Profiler.profile()
def main():
    nb_groups = 4
    group_computer = GroupComputer.from_pixel_distance_radius(
        pixel_distance_radius=6, group_min_size=0, print_step=2000
    )
    spaced_color = SpacedPoints(256, 6)
    sc2 = SpacedPoints(256, 6)
    spaced_position = SpacedPoints32To64(2)
    # spaced_size = SpacedPoints(1024, 4)

    db = load_default_database()
    min_dict = {m.identifier: m for m in db.ensure_miniatures(return_miniatures=True)}
    videos = db.get_videos("readable", "with_thumbnails")
    miniatures = [min_dict[v.filename.path] for v in videos]
    dec_mins = group_computer.batch_compute_groups(miniatures)
    selection = []
    for dec_min in dec_mins:
        groups = dec_min.pixel_groups
        if len(groups) < nb_groups:
            continue
        sorted_groups = sorted(groups, key=lambda g: len(g.members), reverse=True)
        selection.append(
            DecomposedMiniature(dec_min.miniature_identifier, sorted_groups[:nb_groups])
        )
    print(len(videos), "videos(s).")
    print("Similarity", group_computer.similarity)
    print("Before", len(dec_mins))
    _print_stats(dec_mins)
    print("After", len(selection))
    _print_stats(selection)

    with Profiler("Sign"):
        signature_to_identifiers = {}
        for i, dm in enumerate(selection):
            video_signature = []
            for group in dm.pixel_groups:
                color = tuple(
                    spaced_color.nearest_point(value) for value in group.color
                )
                center = tuple(
                    spaced_position.nearest_point(value) for value in group.center
                )
                video_signature.append((color, center))
            video_signature = tuple(sorted(video_signature))
            # video_signature += quad_sign(min_dict[dm.miniature_identifier], sc2)
            signature_to_identifiers.setdefault(video_signature, []).append(
                dm.miniature_identifier
            )
            if (i + 1) % group_computer.print_step == 0:
                print(i + 1, "/", len(selection))
        similarities = {
            s: ids for s, ids in signature_to_identifiers.items() if len(ids) > 1
        }
        print("Found", len(similarities), "similarities.")

    sim_list = list(similarities.values())
    sim_list.sort(key=lambda g: len(g))
    raw_sim = get_raw_similarities()
    if raw_sim:
        ok = []
        na = []
        no = []
        for group in sim_list:
            v = raw_sim.get_groups(group)
            if len(v) == 1 and len(v[0]) == len(group):
                ok.append(group)
            elif len(v):
                na.append(group)
            else:
                no.append(group)
        print("Raw    ", len(raw_sim.group_to_paths))
        print("Ok     ", len(ok))
        print("Partial", len(na))
        print("Falses ", len(no))


    with Profiler("Save"):
        special_property = "<similarity>"
        if  db.has_prop_type(special_property):
            db.remove_prop_type(special_property)
        db.add_prop_type(PropType(special_property, 0, True), False)
        vid_dict = {v.filename.path: v for v in videos}
        for video in videos:
            video.properties[special_property] = []
        for i, ids in enumerate(sim_list):
            for p in ids:
                vid_dict[p].properties[special_property].append(i)
        db.save()


if __name__ == "__main__":
    main()
