from typing import Iterable

from pysaurus.core.classes import StringPrinter
from pysaurus.core.components import AbsolutePath, FileSize, DateModified
from pysaurus.core.constants import PYTHON_ERROR_THUMBNAIL
from pysaurus.core.modules import System


class VideoState:
    __slots__ = (
        # Video properties
        'filename', 'file_size', 'errors', 'video_id',
        # Runtime attributes
        'database', 'rt_is_file', 'rt_size', 'rt_mtime', 'driver_id'
    )
    UNREADABLE = True

    def __init__(self, database, filename=None, size=0, errors=(), video_id=None, from_dictionary=None):
        """
        :type filename: AbsolutePath
        :type size: int
        :type errors: Iterable[str]
        :type video_id: Optional[int]
        :type database: pysaurus.core.database.database.Database
        :type from_dictionary: dict
        """
        if from_dictionary:
            filename = from_dictionary.get('f', filename)
            size = from_dictionary.get('s', size)
            errors = from_dictionary.get('e', errors)
            video_id = from_dictionary.get('j', video_id)
        self.filename = AbsolutePath.ensure(filename)
        self.file_size = size
        self.errors = set(errors)
        self.video_id = video_id

        self.database = database
        self.rt_is_file = False
        self.rt_mtime = 0
        self.rt_size = 0
        self.driver_id = None

    def __str__(self):
        with StringPrinter() as printer:
            printer.write('VideoState:')
            printer.write('\tfilename:  ', self.filename)
            printer.write('\tsize:      ', self.size)
            printer.write('\terrors:    ', ', '.join(sorted(self.errors)) if self.errors else '(none)')
            printer.write('\tvideo_id:  ', self.video_id)
            return str(printer)

    @property
    def unreadable(self):
        return self.UNREADABLE

    @property
    def readable(self):
        return not self.UNREADABLE

    @property
    def error_thumbnail(self):
        return PYTHON_ERROR_THUMBNAIL in self.errors

    @error_thumbnail.setter
    def error_thumbnail(self, has_error):
        if has_error:
            self.errors.add(PYTHON_ERROR_THUMBNAIL)
        elif PYTHON_ERROR_THUMBNAIL in self.errors:
            self.errors.remove(PYTHON_ERROR_THUMBNAIL)

    @property
    def size(self):
        return FileSize(self.file_size)

    @property
    def runtime_size(self):
        return FileSize(self.rt_size)

    @property
    def date(self):
        # runtime date
        return DateModified(self.rt_mtime)

    @property
    def disk(self):
        if System.is_windows():
            return '%s:\\' % (self.filename.path.split(':')[0])
        return self.driver_id

    @property
    def day(self):
        return self.date.day

    def exists(self):
        return self.rt_is_file

    def to_dict(self):
        return {
            'e': list(self.errors),
            'f': self.filename.path,
            'j': self.video_id,
            's': self.file_size,
            'U': self.UNREADABLE,
        }

    @classmethod
    def from_dict(cls, dct, database):
        """
        :type dct: dict
        :type database: pysaurus.core.database.database.Database
        :rtype: VideoState
        """
        return cls(filename=dct['f'],
                   size=dct['s'],
                   errors=dct['e'],
                   video_id=dct.get('j', None),
                   database=database)
