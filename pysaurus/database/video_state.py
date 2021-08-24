from pysaurus.core.classes import StringPrinter, Text, TextWithNumbers
from pysaurus.core.compare import to_comparable
from pysaurus.core.components import AbsolutePath, DateModified, FileSize
from pysaurus.core.constants import PYTHON_ERROR_THUMBNAIL
from pysaurus.database.video_runtime_info import VideoRuntimeInfo
from pysaurus.database.video_sorting import VideoSorting
from pysaurus.core.functions import string_to_pieces


class ClassFlag(property):
    pass


class VideoState:
    __slots__ = (
        # Video properties
        "filename",
        "file_size",
        "errors",
        "video_id",
        # Runtime attributes
        "database",
        "runtime",
        "miniature",
    )
    __protected__ = ("database", "runtime", "miniature")
    UNREADABLE = True

    def __init__(
        self,
        database,
        filename=None,
        size=0,
        errors=(),
        video_id: int = None,
        runtime: VideoRuntimeInfo = None,
        from_dictionary: dict = None,
    ):
        if from_dictionary:
            filename = from_dictionary.get("f", filename)
            size = from_dictionary.get("s", size)
            errors = from_dictionary.get("e", errors)
            video_id = from_dictionary.get("j", video_id)
            runtime = from_dictionary.get("R", runtime)
        self.filename = AbsolutePath.ensure(filename)
        self.file_size = size
        self.errors = set(errors)
        self.video_id = video_id

        self.database = database
        self.runtime = VideoRuntimeInfo.ensure(runtime)
        self.miniature = None

    def __str__(self):
        with StringPrinter() as printer:
            printer.write("VideoState:")
            printer.write("\tfilename:  ", self.filename)
            printer.write("\tsize:      ", self.size)
            printer.write(
                "\terrors:    ",
                ", ".join(sorted(self.errors)) if self.errors else "(none)",
            )
            printer.write("\tvideo_id:  ", self.video_id)
            return str(printer)

    def __hash__(self):
        return hash(self.filename)

    def __eq__(self, other):
        return self.filename == other.filename

    def __lt__(self, other):
        return self.filename < other.filename

    extension = property(lambda self: self.filename.extension)
    file_title = property(lambda self: Text(self.filename.file_title))
    file_title_numeric = property(
        lambda self: TextWithNumbers(self.filename.file_title)
    )
    size = property(lambda self: FileSize(self.file_size))
    day = property(lambda self: self.date.day)
    # runtime attributes
    date = property(lambda self: DateModified(self.runtime.mtime))
    exists = property(lambda self: self.runtime.is_file)
    has_thumbnail = property(
        lambda self: not self.unreadable_thumbnail and self.runtime.has_thumbnail
    )

    readable = ClassFlag(lambda self: not self.UNREADABLE)
    unreadable = ClassFlag(lambda self: self.UNREADABLE)
    found = ClassFlag(lambda self: self.exists)
    not_found = ClassFlag(lambda self: not self.exists)
    with_thumbnails = ClassFlag(lambda self: self.has_thumbnail)
    without_thumbnails = ClassFlag(lambda self: not self.has_thumbnail)

    @property
    def unreadable_thumbnail(self):
        return PYTHON_ERROR_THUMBNAIL in self.errors

    @unreadable_thumbnail.setter
    def unreadable_thumbnail(self, has_error):
        if has_error:
            self.errors.add(PYTHON_ERROR_THUMBNAIL)
        elif PYTHON_ERROR_THUMBNAIL in self.errors:
            self.errors.remove(PYTHON_ERROR_THUMBNAIL)

    @property
    def disk(self):
        disk = self.filename.get_drive_name()
        return disk or self.runtime.driver_id

    def terms(self, as_set=False):
        return string_to_pieces(self.filename.path, as_set=as_set)

    def to_comparable(self, sorting: VideoSorting) -> list:
        return [
            to_comparable(getattr(self, field), reverse) for field, reverse in sorting
        ]

    def to_dict(self):
        return {
            "e": list(self.errors),
            "f": self.filename.path,
            "j": self.video_id,
            "s": self.file_size,
            "U": self.UNREADABLE,
            "R": self.runtime.to_dict(),
        }

    @classmethod
    def from_dict(cls, dct, database):
        return cls(
            filename=dct["f"],
            size=dct["s"],
            errors=dct["e"],
            video_id=dct.get("j", None),
            runtime=dct.get("R", None),
            database=database,
        )

    @classmethod
    def is_flag(cls, name):
        return isinstance(getattr(cls, name), ClassFlag)
