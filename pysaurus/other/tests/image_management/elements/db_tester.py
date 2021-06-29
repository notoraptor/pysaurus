from pysaurus.other.tests.image_management.latest import load_default_database


class DbTester:
    __slots__ = ("db", "videos", "miniatures", "vid_dict", "min_dict")

    def __init__(self):
        self.db = load_default_database()
        self.videos = self.db.get_videos("readable", "with_thumbnails")
        self.min_dict = {m.identifier: m for m in self.db.ensure_miniatures(return_miniatures=True)}
        self.vid_dict = {v.filename.path: v for v in self.videos}
        self.miniatures = [self.min_dict[v.filename.path] for v in self.videos]
