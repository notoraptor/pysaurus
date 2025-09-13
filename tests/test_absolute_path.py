from pysaurus.core.absolute_path import AbsolutePath


def test_reuse_instance():
    path1 = AbsolutePath(".")
    path2 = AbsolutePath(".")
    assert path1 == path2
    assert path1 is not path2
    path3 = AbsolutePath.ensure(path1)
    assert path3 is path1
    path4 = AbsolutePath(str(path1))
    assert path1 == path4
    assert path1 is not path4
