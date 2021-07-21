from pysaurus.core.database.database import Database
from pysaurus.core.database.video import Video
from pysaurus.core.database.video_sorting import VideoSorting
from pysaurus.core.printable import to_table, to_column
from pysaurus.interface.console.api import API
from pysaurus.interface.console.function_parser import FunctionParser


class ConsoleParser(FunctionParser):
    __slots__ = ("api",)

    def __init__(self, list_file_path):
        super(ConsoleParser, self).__init__()
        # Load API.
        self.api = API(Database.load_from_list_file_path(list_file_path, update=False))
        # Update parser from API.
        self.import_from(self.api)
        # Update parser with wrapped functions.
        self.override_from(self)
        self.remove_definitions(
            self.api.clip,
            self.api.clip_from_filename,
            self.api.download_image,
            self.api.download_image_from_filename,
            self.api.videos,
        )
        # Current state check.
        assert len(self.definitions) == 31, len(self.definitions)

    def find(self, terms):
        return to_table(
            self.api.find(terms), Video, ("date", "video_id", "size", "filename")
        )

    def list(self, fields, page_size, page_number):
        sorting = VideoSorting(fields)
        return to_table(
            self.api.list(fields, page_size, page_number),
            Video,
            ["video_id"] + sorting.fields + ["filename"],
        )

    def missing_thumbnails(self):
        return to_table(
            self.api.missing_thumbnails(), Video, ("video_id", "size", "filename")
        )

    def not_found(self):
        return to_table(self.api.not_found(), Video, ("video_id", "filename"))

    def not_found_from_folder(self, folder):
        return to_table(
            self.api.not_found_from_folder(folder), Video, ("video_id", "filename")
        )

    def unreadable(self):
        return to_table(self.api.unreadable(), Video, ("video_id", "size", "filename"))

    def find_batch(self, path):
        batch_results = self.api.find_batch(path)
        lines = []
        for sentence, found in batch_results:
            lines.append(sentence)
            lines.append(
                to_table(found, Video, ("", "date", "video_id", "size", "filename"))
                if found
                else "\t(nothing)"
            )
        return to_column(lines)

    def same_sizes(self):
        duplicated_sizes = self.api.same_sizes()
        lines = []
        for size, elements in duplicated_sizes.items():
            table = to_table(elements, Video, ("size", "video_id", "filename"))
            table.append(
                "",
                "",
                "playlist %s" % (" ".join(str(video.video_id) for video in elements)),
            )
            lines.append(table)
            lines.append("")
        return to_column(lines)
