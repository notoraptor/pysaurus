from typing import Iterable

from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.utils.constants import PYTHON_ERROR_THUMBNAIL


class VideoState:
    __slots__ = ('filename', 'size', 'unreadable', 'errors')

    def __init__(self, filename, size, unreadable, errors):
        # type: (AbsolutePath, int, bool, Iterable[str]) -> None
        self.filename = AbsolutePath.ensure(filename)
        self.size = size
        self.unreadable = unreadable
        self.errors = set(errors)

    @property
    def error_thumbnail(self):
        return PYTHON_ERROR_THUMBNAIL in self.errors

    @error_thumbnail.setter
    def error_thumbnail(self, has_error):
        if has_error:
            self.errors.add(PYTHON_ERROR_THUMBNAIL)
        elif PYTHON_ERROR_THUMBNAIL in self.errors:
            self.errors.remove(PYTHON_ERROR_THUMBNAIL)

    def to_dict(self):
        return {'f': self.filename.path, 's': self.size, 'U': self.unreadable, 'e': self.errors}

    @classmethod
    def from_dict(cls, dct, database):
        del database
        return cls(filename=dct['f'], size=dct['s'], unreadable=dct['U'], errors=dct['e'])
