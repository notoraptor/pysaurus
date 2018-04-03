import os

from pysaurus.utils.absolute_path import AbsolutePath


def test_absolute_path():
    file_path = AbsolutePath(__file__)
    same_file_path = AbsolutePath(__file__)
    direct_dir_path = AbsolutePath(os.path.dirname(__file__))
    inferred_dir_path = file_path.get_dirname()
    fake_path = AbsolutePath(os.path.join(os.path.dirname(__file__), 'a #$%^7 fake file path'))
    assert file_path.path == __file__, file_path.path
    assert file_path.title == 'test_utils', file_path.title
    assert file_path.extension == 'py', file_path.extension
    assert file_path == same_file_path
    assert direct_dir_path == inferred_dir_path
    assert hash(file_path) == hash(same_file_path)
    assert hash(direct_dir_path) == hash(inferred_dir_path)
    assert direct_dir_path.title == 'tests'
    assert direct_dir_path.extension == ''
    assert str(file_path) == file_path.path
    assert direct_dir_path != file_path
    assert direct_dir_path < file_path
    assert direct_dir_path <= file_path
    assert file_path > direct_dir_path
    assert file_path >= direct_dir_path
    assert file_path <= file_path
    assert file_path >= file_path
    assert file_path.exists()
    assert file_path.isfile()
    assert direct_dir_path.exists()
    assert direct_dir_path.isdir()
    assert not fake_path.exists()
    assert file_path.get_basename() == file_path.title + '.' + file_path.extension
    assert AbsolutePath.ensure(__file__) == file_path
    assert AbsolutePath.new_file_path(direct_dir_path, 'test_utils', 'py') == file_path
    assert AbsolutePath.join(direct_dir_path, 'test_utils.py') == file_path
    assert file_path.get_basename() in set(direct_dir_path.listdir())
