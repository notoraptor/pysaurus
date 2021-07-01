from typing import List

from pysaurus.core.database.properties import PropType
from pysaurus.core.miniature_tools.miniature import Miniature
from pysaurus.core.profiling import Profiler
from pysaurus.other.tests.image_management.elements.color_dominance import (
    ColorDominance,
)
from pysaurus.other.tests.image_management.elements.raw_similarities import (
    RawSimilarities,
)
from pysaurus.other.tests.image_management.elements.spaced_points import SpacedPoints
from pysaurus.other.tests.image_management.latest import load_default_database

KEY_TL = "tl"
KEY_TR = "tr"
KEY_BL = "bl"
KEY_BR = "br"
KEY_ALL = "all"
KEY_NAMES = (KEY_TL, KEY_TR, KEY_BL, KEY_BR, KEY_ALL)


def main():
    spaced_color = SpacedPoints(256, 6)
    db = load_default_database()
    min_dict = {m.identifier: m for m in db.ensure_miniatures(return_miniatures=True)}
    videos = db.get_videos("readable", "with_thumbnails")
    vid_dict = {v.filename.path: v for v in videos}
    miniatures = [min_dict[v.filename.path] for v in videos]  # type: List[Miniature]
    classifiers = {key_name: {} for key_name in KEY_NAMES}
    with Profiler("Get color dominance."):
        for i, m in enumerate(miniatures):
            corners = m.get_corner_zones()
            k_tl = ColorDominance.key_from_pixels(corners.tl, spaced_color)
            k_tr = ColorDominance.key_from_pixels(corners.tr, spaced_color)
            k_bl = ColorDominance.key_from_pixels(corners.bl, spaced_color)
            k_br = ColorDominance.key_from_pixels(corners.br, spaced_color)
            key_tl = (k_tl, k_tr, k_bl)
            key_tr = (k_tl, k_tr, k_br)
            key_bl = (k_tl, k_bl, k_br)
            key_br = (k_tr, k_bl, k_br)
            key_all = (k_tl, k_tr, k_bl, k_br)
            classifiers[KEY_TL].setdefault(key_tl, []).append(m)
            classifiers[KEY_TR].setdefault(key_tr, []).append(m)
            classifiers[KEY_BL].setdefault(key_bl, []).append(m)
            classifiers[KEY_BR].setdefault(key_br, []).append(m)
            classifiers[KEY_ALL].setdefault(key_all, []).append(m)
            if (i + 1) % 1000 == 0:
                print(i + 1, "/", len(miniatures))
    for key_name in KEY_NAMES:
        print("====", key_name, "====")
        classifiers[key_name] = {
            k: ms for k, ms in classifiers[key_name].items() if len(ms) > 1
        }
        nb_videos = sum(len(vs) for vs in classifiers[key_name].values())
        print(
            len(classifiers[key_name]),
            "keys,",
            nb_videos,
            "videos,",
            nb_videos / len(classifiers[key_name]),
            "per key",
        )
        print("min", min(len(vs) for vs in classifiers[key_name].values()))
        print("max", max(len(vs) for vs in classifiers[key_name].values()))

    with Profiler("Save"):
        special_property = "<similarity>"
        if db.has_prop_type(special_property):
            db.remove_prop_type(special_property)
        db.add_prop_type(PropType(special_property, "", True), False)
        for video in videos:
            video.properties[special_property] = []
        for key_name in KEY_NAMES:
            for i, ms in enumerate(classifiers[key_name].values()):
                for m in ms:
                    vid_dict[m.identifier].properties[special_property].append(
                        f"{key_name}_{i}"
                    )
        rs = RawSimilarities.new()
        if rs:
            for i, ps in enumerate(rs.group_to_paths):
                ps = [p for p in ps if p in vid_dict]
                if len(ps) < 2:
                    continue
                for p in ps:
                    vid_dict[p].properties[special_property].append(str(-i))
        db.save()


if __name__ == "__main__":
    main()
