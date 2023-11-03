import logging
from typing import Dict, Iterable, List, Sequence

from pysaurus.core import functions
from pysaurus.core.components import AbsolutePath
from pysaurus.core.profiling import Profiler
from pysaurus.database.jsdb.inter_json_database import InterJsonDatabase
from pysaurus.video import Video
from pysaurus.video.video_sorting import VideoSorting

logger = logging.getLogger(__name__)


class JsonDatabase(InterJsonDatabase):
    """With methods used in database provider."""

    def search(
        self, text: str, cond: str = "and", videos: Sequence[int] = None
    ) -> Iterable[int]:
        if text:
            self._jsondb_flush_changes()
            if videos is None:
                filenames: Dict[AbsolutePath, Video] = self._videos
            else:
                filenames: Dict[AbsolutePath, Video] = {
                    self._id_to_video[video_id].filename: self._id_to_video[video_id]
                    for video_id in videos
                }
            terms = functions.string_to_pieces(text)
            if cond == "exact":
                with Profiler(f"query exact: {text}", self.notifier):
                    selection = (
                        filename
                        for filename in self._indexer.query_and(filenames, terms)
                        if self._videos[filename].has_exact_text(text)
                    )
            elif cond == "and":
                selection = self._indexer.query_and(filenames, terms)
            elif cond == "or":
                selection = self._indexer.query_or(filenames, terms)
            else:
                assert cond == "id"
                (term,) = terms
                video_id = int(term)
                selection = (
                    [self._id_to_video[video_id].filename]
                    if video_id in self._id_to_video
                    else []
                )
            return (filenames[filename].video_id for filename in selection)
        return ()

    def sort_video_indices(self, indices: Iterable[int], sorting: VideoSorting):
        return sorted(
            indices,
            key=lambda video_id: self._id_to_video[video_id].to_comparable(sorting),
        )

    def default_prop_unit(self, name):
        (pt,) = self.select_prop_types(name=name)
        return None if pt["multiple"] else pt["defaultValue"]

    def __unused_clean_thumbnails(self, paths: List[AbsolutePath]):
        self._thumb_mgr.clean_thumbnails(paths)
