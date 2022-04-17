from pysaurus.core.classes import StringPrinter, Text
from pysaurus.core.compare import to_comparable
from pysaurus.core.components import AbsolutePath, DateModified, FileSize
from pysaurus.core.constants import PYTHON_ERROR_THUMBNAIL
from pysaurus.core.functions import class_get_public_attributes, string_to_pieces
from pysaurus.core.jsonable import Jsonable
from pysaurus.database.semantic_text import SemanticText
from pysaurus.database.video_runtime_info import VideoRuntimeInfo
from pysaurus.database.video_sorting import VideoSorting


class VideoState(Jsonable):
    filename: ("f", str) = None
    file_size: "s" = 0
    errors: "e" = set()
    video_id: ("j", int) = None
    runtime: ("R", VideoRuntimeInfo) = {}
    unreadable: "U" = True
    thumb_name: "i" = ""
    __slots__ = ("discarded",)
    __protected__ = ("database", "runtime", "discarded")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.discarded = False

    def __str__(self):
        cls = type(self)
        with StringPrinter() as printer:
            printer.write(f"{cls.__name__} {self.video_id}:")
            for field in class_get_public_attributes(cls):
                printer.write(f"\t{field}: {getattr(self, field)}")
            return str(printer)

    def __hash__(self):
        return hash(self.filename)

    def __eq__(self, other):
        return self.filename == other.filename

    def __lt__(self, other):
        return self.filename < other.filename

    def get_filename(self):
        return AbsolutePath(self.__json__["filename"])

    def set_filename(self, data):
        assert isinstance(data, (str, AbsolutePath))
        self.__json__["filename"] = str(data)

    def get_thumb_name(self):
        from pysaurus.database.db_utils import generate_thumb_name

        return generate_thumb_name(self.filename)

    def to_dict_errors(self, errors):
        return list(errors)

    @classmethod
    def from_dict_errors(cls, errors):
        return set(errors)

    extension = property(lambda self: self.filename.extension)
    file_title = property(lambda self: Text(self.filename.file_title))
    file_title_numeric = property(lambda self: SemanticText(self.filename.file_title))
    size = property(lambda self: FileSize(self.file_size))
    day = property(lambda self: self.date.day)
    # runtime attributes
    disk = property(
        lambda self: self.filename.get_drive_name() or self.runtime.driver_id
    )
    date = property(lambda self: DateModified(self.runtime.mtime))
    has_thumbnail = property(
        lambda self: not self.unreadable_thumbnail and self.runtime.has_thumbnail
    )

    readable = property(lambda self: not self.unreadable)
    found = property(lambda self: self.runtime.is_file)
    not_found = property(lambda self: not self.runtime.is_file)
    with_thumbnails = property(lambda self: self.has_thumbnail)
    without_thumbnails = property(lambda self: not self.has_thumbnail)

    @property
    def unreadable_thumbnail(self):
        return PYTHON_ERROR_THUMBNAIL in self.errors

    @unreadable_thumbnail.setter
    def unreadable_thumbnail(self, has_error):
        if has_error:
            self.errors.add(PYTHON_ERROR_THUMBNAIL)
        elif PYTHON_ERROR_THUMBNAIL in self.errors:
            self.errors.remove(PYTHON_ERROR_THUMBNAIL)

    def terms(self, as_set=False):
        return string_to_pieces(self.filename.path, as_set=as_set)

    def to_comparable(self, sorting: VideoSorting) -> list:
        return [
            to_comparable(getattr(self, field), reverse) for field, reverse in sorting
        ]

    @classmethod
    def is_flag(cls, name):
        return name in {
            "readable",
            "unreadable",
            "found",
            "not_found",
            "with_thumbnails",
            "without_thumbnails",
        }
