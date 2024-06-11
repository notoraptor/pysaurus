import os


def _validate_file(path: str) -> str:
    assert os.path.isfile(path)
    return path


FOLDER_FONT = os.path.abspath(os.path.join(os.path.dirname(__file__)))

FOLDER_SOURCE_SANS = os.path.join(FOLDER_FONT, "source-sans", "TTF")

PATH_SOURCE_SANS_REGULAR = _validate_file(
    os.path.join(FOLDER_SOURCE_SANS, "SourceSans3-Regular.ttf")
)

PATH_SOURCE_SANS_LIGHT = _validate_file(
    os.path.join(FOLDER_SOURCE_SANS, "SourceSans3-Light.ttf")
)

PATH_SOURCE_HAN_SANS_JP = _validate_file(os.path.join(FOLDER_FONT, "SourceHanSans-VF.ttf"))
PATH_SOURCE_HAN_SANS_TTC = _validate_file(os.path.join(FOLDER_FONT, "SourceHanSans-VF.ttf.ttc"))
