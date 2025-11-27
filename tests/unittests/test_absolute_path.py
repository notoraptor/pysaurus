import os

from pysaurus.core.absolute_path import AbsolutePath


def test_absolute_path():
    wd = os.path.abspath("..")
    ap = AbsolutePath("..")
    assert wd == ap.standard_path

    sd = os.path.abspath(__file__)
    sp = AbsolutePath(__file__)
    assert sd == sp.standard_path


def test_reuse_instance():
    path1 = AbsolutePath("..")
    path2 = AbsolutePath("..")
    assert path1 == path2
    assert path1 is not path2
    path3 = AbsolutePath.ensure(path1)
    assert path3 is path1
    path4 = AbsolutePath(str(path1))
    assert path1 == path4
    assert path1 is not path4


def test_join():
    path1 = AbsolutePath("a/b/c")
    path2 = AbsolutePath("a/b") / "c"
    path3 = AbsolutePath("a") / "b" / "c"
    assert path1 == path2
    assert path1 == path3
