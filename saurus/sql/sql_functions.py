from pysaurus.core.components import AbsolutePath
from pysaurus.core.semantic_text import pad_numbers_in_string


def pysaurus_get_disk(filename: str, driver_id: int) -> str:
    return AbsolutePath(filename).get_drive_name() or str(driver_id)


def pysaurus_get_extension(filename: str) -> str:
    return AbsolutePath(filename).extension


def pysaurus_get_file_title(filename: str) -> str:
    return AbsolutePath(filename).file_title


def pysaurus_get_title(filename: str, meta_title: str) -> str:
    return meta_title or AbsolutePath(filename).file_title


def pysaurus_text_with_numbers(text: str, padding: int) -> str:
    return pad_numbers_in_string(text, padding)
