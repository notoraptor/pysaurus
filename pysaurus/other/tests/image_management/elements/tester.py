from typing import Dict, List

from pysaurus.core.database.database import Database
from pysaurus.core.database.video import Video
from pysaurus.core.miniature import Miniature
from pysaurus.core.testing import TEST_LIST_FILE_PATH


class Tester:
    __slots__ = (
        "files",
        "database",
        "videos",
        "videos_dict",
        "vid_to_v",
        "min_dict",
        "miniatures",
    )

    def __init__(self, update=False, video_filenames=()):
        database = Database.load_from_list_file_path(TEST_LIST_FILE_PATH, update=update)
        if video_filenames:
            videos = []
            for filename in video_filenames:
                video = database.get_video_from_filename(filename)
                assert video, filename
                videos.append(video)
        else:
            videos = list(database.readable.found.with_thumbnails) + list(
                database.readable.not_found.with_thumbnails
            )
        videos_dict = {v.filename.path: v for v in videos}
        vid_to_v = {v.video_id: v for v in videos}
        min_dict = {
            m.identifier: m for m in database.ensure_miniatures(return_miniatures=True)
        }
        miniatures = [min_dict[video.filename.path] for video in videos]
        self.files = video_filenames
        self.database = database  # type: Database
        self.videos = videos  # type: List[Video]
        self.videos_dict = videos_dict  # type: Dict[str, Video]
        self.vid_to_v = vid_to_v  # type: Dict[int, Video]
        self.min_dict = min_dict  # type: Dict[str, Miniature]
        self.miniatures = miniatures  # type: List[Miniature]
