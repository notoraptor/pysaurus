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
        cls, miniatures_path: AbsolutePath, version: int
    ) -> dict[AbsolutePath, Miniature]:
        """Load the miniatures written for this database version.

        A file stamped with another version is dropped rather than read: it
        holds paths spelled the way that version stored them (migration m0006
        rewrites mount points), and a stale spelling is indistinguishable from
        a valid one. It is only a cache, so ensure_miniatures regenerates what
        it needs on the next call.
        """
        if not miniatures_path.exists():
            return {}
        try:
            with open(miniatures_path.assert_file().path) as miniatures_file:
                content = json.load(miniatures_file)
        except ValueError:
            content = None
        if not isinstance(content, dict) or content.get("version") != version:
            # Another version, or the pre-versioning format (a bare array).
            miniatures_path.delete()
            return {}
        entries = content.get("miniatures")
        if not isinstance(entries, list):
            raise exceptions.InvalidMiniaturesJSON(miniatures_path)
        miniatures = {}
        for dct in entries:
            m = Miniature.from_dict(dct)
            assert m.identifier is not None
            miniatures[AbsolutePath(m.identifier)] = m
        return miniatures

    @classmethod
    def write_miniatures_file(
        cls, miniatures_path: AbsolutePath, version: int, miniatures
    ) -> None:
        with open(miniatures_path.path, "w") as output_file:
            json.dump(
                {"version": version, "miniatures": [m.to_dict() for m in miniatures]},
                output_file,
            )

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
