from typing import List

from pysaurus.other.tests.image_management.test_utils import Tester

from pysaurus.core.classes import Table
from pysaurus.core.miniature import Miniature
from pysaurus.other.tests.image_management.elements.draw import (
    Draw,
    dilate_miniature_data,
)
from pysaurus.other.tests.image_management.elements.group_computer import GroupComputer
from pysaurus.other.tests.image_management.elements.spaced_points import (
    SpacedPoints,
    SpacedPoints32To64,
)


class ColorIterator:
    def __init__(self, step=1):
        assert 256 % step == 0
        start = step - 1
        self.step = step
        self.r = start
        self.g = start
        self.b = start

    def is_white(self):
        return self.r == self.g == self.b == 255

    def next(self):
        current = self.r, self.g, self.b
        self.b += self.step
        if self.b // 256:
            self.b %= 256
            self.g += self.step
            if self.g // 256:
                self.g %= 256
                self.r += self.step
                if self.r // 256:
                    self.r %= 256
        return current


def simplify_images(
    miniatures: List[Miniature], group_min_size=1, pixel_distance_radius=1
):
    similarity_percent = (255 - pixel_distance_radius) * 100 / 255
    group_computer = GroupComputer(
        group_min_size=group_min_size, similarity_percent=similarity_percent
    )
    group_packs = [group_computer.compute_groups(m) for m in miniatures]
    simplified_data = []
    for i in range(len(miniatures)):
        miniature = miniatures[i]
        group_pack = group_packs[i]
        print(
            "Miniature",
            i,
            "grouped count",
            sum(len(g.members) for g in group_pack),
            "/",
            miniature.width * miniature.height,
        )
        data = [(0, 0, 0)] * miniature.width * miniature.height
        color_iterator = ColorIterator(2 ** 6)
        colors = [color_iterator.next() for _ in range(len(group_pack))]
        for group_id, group in enumerate(group_pack):
            color = colors[group_id]
            for identifier in group.members:
                data[identifier] = color
        simplified_data.append(data)
    return simplified_data, group_packs


CLASSIFIER_DEFAULT = "default"
CLASSIFIER_INTERVALS = "intervals"
CLASSIFIER_SUB_INTERVALS = "sub_intervals"
CLASSIFIER_RAW = "raw"


class Run(Tester):
    __slots__ = ()

    def __init__(self, files: List[str]):
        super().__init__(video_filenames=[t[1] for t in files])
        self.files = files

    def run(
        self,
        group_min_size=1,
        pixel_distance_radius=8,
        nb_color_points=64,
        nb_position_points=8,
        nb_size_points=256,
        classifier=CLASSIFIER_INTERVALS,
    ):
        simplified_data, group_packs = simplify_images(
            self.miniatures,
            group_min_size=group_min_size,
            pixel_distance_radius=pixel_distance_radius,
        )

        if classifier == CLASSIFIER_DEFAULT:
            spaced_color = SpacedPoints(256, nb_color_points)
            spaced_position = SpacedPoints32To64(nb_position_points)
            spaced_size = SpacedPoints(1024, nb_size_points)
            callback = lambda g: g.to_basic_group(
                spaced_color, spaced_position, spaced_size
            )
        elif classifier == CLASSIFIER_INTERVALS:
            callback = lambda g: g.to_basic_group_intervals(
                nb_color_points, nb_position_points, nb_size_points
            )
        elif classifier == CLASSIFIER_SUB_INTERVALS:
            callback = lambda g: g.to_basic_group_sub_intervals(
                nb_color_points, nb_position_points, nb_size_points
            )
        elif classifier == CLASSIFIER_RAW:
            callback = lambda g: g.to_basic_group_raw()
        else:
            raise ValueError(f"Unknown group classifier option: {classifier}")

        pg_to_bg = {}
        basic_groups = set()
        nb_pg = 0
        unique_id = 0
        for group_pack in group_packs:
            nb_pg += len(group_pack)
            for pixel_group in group_pack:
                pixel_group.identifier = unique_id
                unique_id += 1
                bg = callback(pixel_group)
                pg_to_bg[pixel_group] = bg
                basic_groups.add(bg)

        assert nb_pg == len(pg_to_bg), (nb_pg, len(pg_to_bg))
        print("Classifier", classifier)
        print("Nb. images", len(self.miniatures))
        print("Nb. pixel groups", nb_pg)
        print("Nb. basic groups", len(basic_groups))
        basic_groups = sorted(basic_groups)
        color_iterator = ColorIterator(2 ** 4)
        basic_colors = [color_iterator.next() for _ in range(len(basic_groups))]
        assert len(set(basic_colors)) == len(basic_groups)
        bg_to_color = {bg: color for (bg, color) in zip(basic_groups, basic_colors)}

        printable_lines = []
        similarities = []

        for i in range(len(self.miniatures)):
            for j in range(i + 1, len(self.miniatures)):
                pi = group_packs[i]
                pj = group_packs[j]
                bi = [pg_to_bg[p] for p in pi]
                bj = [pg_to_bg[p] for p in pj]
                li = sum(len(p.members) for p in pi)
                lj = sum(len(p.members) for p in pj)
                ici = [x for x, b in enumerate(bi) if b in bj]
                icj = [x for x, b in enumerate(bj) if b in bi]
                ci = sum(len(pi[x].members) for x in ici)
                cj = sum(len(pj[x].members) for x in icj)
                ni = self.files[i][0]
                nj = self.files[j][0]
                line = [
                    f"Compare: {ni}-{nj}",
                    ci,
                    "/",
                    li,
                    ci * 100 / li,
                    "%",
                    f"Compare: {nj}-{ni}",
                    cj,
                    "/",
                    lj,
                    cj * 100 / lj,
                    "%",
                    ni,
                    nj,
                    ci * 100 / li >= 50,
                    cj * 100 / lj >= 50,
                ]
                printable_lines.append(line)
                if ci * 100 / li >= 50:
                    similarities.append((ni, nj))
                if cj * 100 / lj >= 50:
                    similarities.append((nj, ni))
        print(Table([""] * len(printable_lines[0]), printable_lines))

        dec = 4
        surface = Draw(
            128 * len(self.miniatures) + dec * (len(self.miniatures) - 1),
            128 * 3 + dec * 2,
        )
        for i in range(len(self.miniatures)):
            m = self.miniatures[i]
            g = group_packs[i]
            d = [(0, 0, 0)] * m.width * m.height
            for pg in g:
                bg = pg_to_bg[pg]
                cl = bg_to_color[bg]
                for identifier in pg.members:
                    d[identifier] = cl
            m_data = dilate_miniature_data(list(m.data()), m.width, m.height)
            s_data = dilate_miniature_data(simplified_data[i], m.width, m.height)
            d_prim = dilate_miniature_data(d, m.width, m.height)
            surface.draw_data(m_data, 128, 128, i * (128 + dec), 0)
            surface.draw_data(s_data, 128, 128, i * (128 + dec), 128 + dec)
            surface.draw_data(d_prim, 128, 128, i * (128 + dec), 2 * (128 + dec))
        surface.display()
        return similarities


if __name__ == "__main__":
    _files = [
        (
            "a1",
            r"J:\donnees\divers\autres\p\[HD, 1920x1080p] Fucked and Oiled Up - Susy Gala  HD-Porn.me.mp4",
        ),
        (
            "a2",
            r"Q:\donnees\autres\p\Susy Gala - Fucked And Oiled Up - Ready Or Not Here I Cum #bigtits.mp4",
        ),
        (
            "a3",
            r"Q:\donnees\autres\p\Susy Gala - Nacho's First Class Fucks (2016) #POV.mp4",
        ),
        (
            "b1",
            r"J:\donnees\divers\autres\p\Hannah Hays - Biggest Black Cock - XFREEHD.mp4",
        ),
        ("b2", r"M:\donnees\autres\p\Hannah Hays - Interracial Pickups.mp4"),
        ("b3", r"Q:\donnees\autres\p\Hannah Hays_2.mp4"),
        (
            "c1",
            r"J:\donnees\divers\autres\p\Daya Knight - black teacher helping little boy study - 1080.mp4",
        ),
        ("c2", r"L:\donnees\autres\p\Daya Knight - bkb16158-1080p.mp4"),
        ("c3", r"M:\donnees\autres\p\daya knight - Young Guy Fucks Ebony Lady.mp4"),
        (
            "d1",
            r"E:\donnees\autres\p\busty-asian-real-estate-agent-gets-her-pussy-destroyed_1080p.mp4",
        ),
        ("d2", r"J:\donnees\divers\autres\p\Mena Li and a big black cock__p720.mp4"),
        (
            "d3",
            r"M:\donnees\autres\p\mena li - Asian pussy gets destroyed with a BBC__p720.mp4",
        ),
        (
            "d4",
            r"R:\donnees\autres\p\mena li - Scene 2 From Chocolate Desires - 1080p.mp4",
        ),
    ]
    # main(
    #     _files,
    #     group_min_size=1,
    #     nb_color_points=8,
    #     nb_position_points=4,
    #     nb_size_points=4,
    #     pixel_distance_radius=10,
    #     classifier=CLASSIFIER_INTERVALS,
    # )
    run = Run(_files)
    s1 = run.run(
        group_min_size=1,
        nb_color_points=8,
        nb_position_points=4,
        nb_size_points=4,
        pixel_distance_radius=6,
        classifier=CLASSIFIER_INTERVALS,
    )
    s2 = run.run(
        group_min_size=1,
        nb_color_points=8,
        nb_position_points=4,
        nb_size_points=4,
        pixel_distance_radius=6,
        classifier=CLASSIFIER_SUB_INTERVALS,
    )
    s = set(s1 + s2)
    cs = []
    for x, y in s:
        if (y, x) in s:
            cs.append(tuple(sorted((x, y))))
    if cs:
        print("Valid:")
        for x, y in sorted(set(cs)):
            print(x, y)
