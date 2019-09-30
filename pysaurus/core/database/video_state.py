from typing import Iterable, Optional

from pysaurus.core.classes import StringPrinter
from pysaurus.core.components import AbsolutePath, FileSize
from pysaurus.core.constants import PYTHON_ERROR_THUMBNAIL


class VideoState:
    __slots__ = ('filename', 'size', 'unreadable', 'errors', 'video_id')

    def __init__(self, filename, size, unreadable, errors, video_id):
        # type: (AbsolutePath, int, bool, Iterable[str], Optional[int]) -> None
        self.filename = AbsolutePath.ensure(filename)
        self.size = size
        self.unreadable = unreadable
        self.errors = set(errors)
        self.video_id = video_id

    def __str__(self):
        with StringPrinter() as printer:
            printer.write('VideoState:')
            printer.write('\tfilename:  ', self.filename)
            printer.write('\tsize:      ', self.get_size())
            printer.write('\tunreadable:', self.unreadable)
            printer.write('\terrors:    ', ', '.join(sorted(self.errors)) if self.errors else '(none)')
            printer.write('\tvideo_id:  ', self.video_id)
            return str(printer)

    @property
    def error_thumbnail(self):
        return PYTHON_ERROR_THUMBNAIL in self.errors

    @error_thumbnail.setter
    def error_thumbnail(self, has_error):
        if has_error:
            self.errors.add(PYTHON_ERROR_THUMBNAIL)
        elif PYTHON_ERROR_THUMBNAIL in self.errors:
            self.errors.remove(PYTHON_ERROR_THUMBNAIL)

    def get_size(self):
        return FileSize(self.size)

    def to_dict(self):
        return {'f': self.filename.path, 's': self.size, 'U': self.unreadable, 'e': self.errors, 'j': self.video_id}

    @classmethod
    def from_dict(cls, dct, database):
        del database
        return cls(filename=dct['f'], size=dct['s'], unreadable=dct['U'], errors=dct['e'], video_id=dct.get('j', None))
