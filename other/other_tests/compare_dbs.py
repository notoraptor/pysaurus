from typing import List

from pysaurus.core.components import AbsolutePath
from pysaurus.core.json_backup import JsonBackup
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.database.db_way_def import DbWays
from pysaurus.database.jsdb.jsdbvideo.lazy_video import LazyVideo as Video
from saurus.sql.pysaurus_program import PysaurusProgram


def get_db_data(db_path: AbsolutePath) -> List[Video]:
    ways = DbWays(db_path)
    json_backup = JsonBackup(ways.db_json_path, DEFAULT_NOTIFIER)
    json_dict = json_backup.load()
    assert isinstance(json_dict, dict)
    videos = sorted(
        Video(None, video_dict) for video_dict in json_dict.get("videos", ())
    )
    return videos


def _stats(db_name: str, videos: List[Video]):
    print(f"[stats/{db_name}]", len(videos))
    for source in [
        # ["discarded"],
        ["readable"],
        ["unreadable"],
        # ["not_found"]
    ]:
        selection = [
            video for video in videos if all(getattr(video, flag) for flag in source)
        ]
        print(f"{', '.join(source)}:", len(selection))


def main():
    program = PysaurusProgram()
    path_db1 = AbsolutePath.join(program.dbs_dir, "test")
    path_db2 = AbsolutePath.join(program.dbs_dir, "test 2")
    assert path_db1.isdir()
    assert path_db2.isdir()
    db1_name = path_db1.title
    db2_name = path_db2.title
    db1_videos = get_db_data(path_db1)
    db2_videos = get_db_data(path_db2)
    _stats(db1_name, db1_videos)
    _stats(db2_name, db2_videos)


if __name__ == "__main__":
    main()
