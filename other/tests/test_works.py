from pysaurus.core.components import AbsolutePath
from pysaurus.database.jobs_python import collect_video_paths


def test():
    collect_video_paths([AbsolutePath(r"c:\data\autres\p")])
