from typing import Dict, List, Sequence, Tuple

import ujson as json

from pysaurus.application import exceptions
from pysaurus.core.components import AbsolutePath
from pysaurus.core.informer import Informer
from pysaurus.core.parallelization import parallelize
from pysaurus.database import jobs_python
from pysaurus.miniature.group_computer import GroupComputer
from pysaurus.miniature.miniature import Miniature


class Miniatures:
    @classmethod
    def read_miniatures_file(
        cls, miniatures_path: AbsolutePath
    ) -> Dict[AbsolutePath, Miniature]:
        miniatures = {}
        if miniatures_path.exists():
            with open(miniatures_path.assert_file().path) as miniatures_file:
                json_array = json.load(miniatures_file)
            if not isinstance(json_array, list):
                raise exceptions.InvalidMiniaturesJSON(miniatures_path)
            for dct in json_array:
                m = Miniature.from_dict(dct)
                miniatures[AbsolutePath(m.identifier)] = m
        return miniatures

    @classmethod
    def get_miniatures(
        cls, named_thumbnails: Sequence[Tuple[AbsolutePath, bytes]]
    ) -> List[Miniature]:
        return list(
            parallelize(
                jobs_python.generate_video_miniature,
                named_thumbnails,
                notifier=Informer.default(),
                kind="video miniature(s)",
                progress_step=100,
            )
        )

    @classmethod
    def update_group_signatures(
        cls, miniatures: Dict[str, Miniature], pixel_distance_radius, group_min_size
    ):
        m_no_groups = [
            m
            for m in miniatures.values()
            if not m.has_group_signature(pixel_distance_radius, group_min_size)
        ]
        if m_no_groups:
            group_computer = GroupComputer(
                group_min_size=group_min_size,
                pixel_distance_radius=pixel_distance_radius,
            )
            for dm in group_computer.batch_compute_groups(
                m_no_groups, notifier=Informer.default()
            ):
                miniatures[dm.miniature_identifier].set_group_signature(
                    pixel_distance_radius, group_min_size, len(dm.pixel_groups)
                )
