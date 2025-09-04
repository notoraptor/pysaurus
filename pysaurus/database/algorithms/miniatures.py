from typing import Sequence

import ujson as json

from pysaurus.application import exceptions
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.informer import Information
from pysaurus.core.miniature import Miniature
from pysaurus.core.modules import ImageUtils
from pysaurus.core.parallelization import parallelize


class Miniatures:
    @classmethod
    def read_miniatures_file(
        cls, miniatures_path: AbsolutePath
    ) -> dict[AbsolutePath, Miniature]:
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
        cls, named_thumbnails: Sequence[tuple[AbsolutePath, bytes]]
    ) -> list[Miniature]:
        return list(
            parallelize(
                cls._gen_miniature,
                named_thumbnails,
                notifier=Information.notifier(),
                kind="video miniature(s)",
                progress_step=100,
            )
        )

    @classmethod
    def _gen_miniature(cls, file_name: AbsolutePath, thumb_data: bytes) -> Miniature:
        return Miniature.from_file_data(
            thumb_data, ImageUtils.THUMBNAIL_SIZE, file_name.path
        )
