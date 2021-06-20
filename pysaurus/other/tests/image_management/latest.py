from typing import List

from pysaurus.core.database.database import Database
from pysaurus.core.database.properties import PropType
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


def _print_stats(decomposed_miniatures: List[DecomposedMiniature]):
    nb_min_groups = min(len(dm.pixel_groups) for dm in decomposed_miniatures)
    nb_max_groups = max(len(dm.pixel_groups) for dm in decomposed_miniatures)
    nb_min_size = min(
        len(g.members) for dm in decomposed_miniatures for g in dm.pixel_groups
    )
    nb_max_size = max(
        len(g.members) for dm in decomposed_miniatures for g in dm.pixel_groups
    )
    print("Nb groups", nb_min_groups, "to", nb_max_groups)
    print("Group size", nb_min_size, "to", nb_max_size)


@Profiler.profile()
def main():
    db = load_default_database()
    min_dict = {m.identifier: m for m in db.ensure_miniatures(return_miniatures=True)}
    videos = db.get_videos("readable", "with_thumbnails")
    miniatures = [min_dict[v.filename.path] for v in videos]
    group_computer = GroupComputer.from_pixel_distance_radius(
        pixel_distance_radius=8, group_min_size=0, print_step=1000
    )
    decomposed_miniatures = group_computer.batch_compute_groups(miniatures)
    selection = []
    for decomped_miniature in decomposed_miniatures:
        groups = decomped_miniature.pixel_groups
        if len(groups) < 4:
            continue
        sorted_groups = sorted(groups, key=lambda g: len(g.members), reverse=True)
        selected_groups = sorted_groups[:4]
        assert len(selected_groups) == 4
        selection.append(
            DecomposedMiniature(
                decomped_miniature.miniature_identifier, selected_groups
            )
        )
    print(len(miniatures), "videos(s).")
    print("Similarity", group_computer.similarity)
    print("Before", len(decomposed_miniatures))
    _print_stats(decomposed_miniatures)
    print("After", len(selection))
    _print_stats(selection)

    with Profiler("Sign"):
        spaced_color = SpacedPoints(256, 6)
        spaced_position = SpacedPoints32To64(2)
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
            signature_to_identifiers.setdefault(video_signature, []).append(
                dm.miniature_identifier
            )
            if (i + 1) % 1000 == 0:
                print(i + 1, "/", len(selection))
        similarities = {
            s: ids for s, ids in signature_to_identifiers.items() if len(ids) > 1
        }
        print(
            "Found",
            len(similarities),
            "similaritie(s) on",
            len(selection),
            "video(s) selected over",
            len(decomposed_miniatures),
        )

    with Profiler("Save"):
        special_property = "<similarity>"
        prop_type = PropType(special_property, "", True)
        if not db.has_prop_type(special_property):
            db.add_prop_type(prop_type, False)
        vid_dict = {v.filename.path: v for v in videos}
        for video in videos:
            video.properties[special_property] = []
        for i, (sim, ids) in enumerate(similarities.items()):
            for p in ids:
                vid_dict[p].properties[special_property].append(str(i))
        db.save()


if __name__ == "__main__":
    main()
