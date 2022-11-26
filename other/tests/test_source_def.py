from pysaurus.database.viewport.source_def import SourceDef
from .utils_testing import get_database


def test_source_def():
    sd = SourceDef(
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
    vs = db.get_videos("readable")
    vsf = db.get_videos("unreadable", "found")
    assert vs
    assert vsf
    assert sd.contains_video(vs[0])
    assert not sd.contains_video(vsf[0])
