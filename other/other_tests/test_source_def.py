from pysaurus.database.jsdb.jsdbvideo.lazy_video import LazyVideo as Video
from pysaurus.video_provider.source_def import SourceDef, SourceFlag
from tests.utils_testing import get_database


class ExtendedSourceFlag(SourceFlag):
    __slots__ = ()

    def contains_flag(self, flag):
        return self.flag == flag or any(
            child.contains_flag(flag) for child in self.children.values()
        )

    def contains_video(self, video: Video):
        return getattr(video, self.flag) and (
            not self.children
            or any(child.contains_video(video) for child in self.children.values())
        )

    def has_path_without(self, flag):
        return self.flag != flag and (
            not self.children
            or any(child.has_path_without(flag) for child in self.children.values())
        )


class ExtendedSourceDef(SourceDef):
    __slots__ = ()
    __SOURCE_FLAG_CLASS__ = ExtendedSourceFlag

    def contains_flag(self, flag: str) -> bool:
        return any(child.contains_flag(flag) for child in self.children.values())

    def contains_video(self, video: Video) -> bool:
        return any(child.contains_video(video) for child in self.children.values())

    def has_source_without(self, flag):
        return any(child.has_path_without(flag) for child in self.children.values())


def test_source_def():
    sd = ExtendedSourceDef(
        [
            ("readable", "found", "with_thumbnails"),
            ("readable", "not_found", "with_thumbnails"),
            ("unreadable", "not_found", "with_thumbnails"),
        ]
    )

    assert str(sd) == (
        "[readable[found[with_thumbnails], not_found[with_thumbnails]], "
        "unreadable[not_found[with_thumbnails]]]"
    )
    assert sd.contains_flag("readable")
    assert sd.contains_flag("found")
    assert sd.contains_flag("not_found")
    assert sd.contains_flag("with_thumbnails")
    assert sd.contains_flag("unreadable")
    assert not sd.contains_flag("without_thumbnails")

    assert sd.has_source_without("found")
    assert sd.has_source_without("not_found")
    assert not sd.has_source_without("with_thumbnails")

    db = get_database()
    vs = db._jsondb_get_cached_videos("readable")
    vsf = db._jsondb_get_cached_videos("unreadable", "found")
    assert vs
    assert vsf
    assert sd.contains_video(vs[0])
    assert not sd.contains_video(vsf[0])
