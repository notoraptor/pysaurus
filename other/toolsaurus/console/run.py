import os
from typing import Dict, List, Tuple

import other.toolsaurus.functions
import pysaurus.application.application
import pysaurus.application.utils
from other.toolsaurus.command_line_interface import command_line_interface
from other.toolsaurus.database.database import ExtendedDatabase
from other.toolsaurus.function_parser import FunctionParser, fdef, fsigned
from other.toolsaurus.printable import to_column, to_table
from pysaurus.core import functions
from pysaurus.core.classes import StringPrinter
from pysaurus.core.components import AbsolutePath, Duration, FileSize
from pysaurus.core.modules import ImageUtils, VideoClipping
from pysaurus.database.utils import generate_temp_file_path
from pysaurus.database.video import Video
from pysaurus.database.video_features import VideoFeatures
from pysaurus.database.video_sorting import VideoSorting
from pysaurus.database.viewport.view_tools import SearchDef

TEST_LIST_FILE_PATH = AbsolutePath(
    os.path.join(
        pysaurus.application.utils.package_dir(),
        "../../../pysaurus",
        "..",
        ".local",
        ".local",
        "test_folder.log",
    )
)


def path_in_directory(self: AbsolutePath, directory, is_case_insensitive=None):
    directory = AbsolutePath.ensure(directory)
    if not directory.isdir():
        return False
    directory = directory.standard_path
    path = self.standard_path
    if is_case_insensitive:
        directory = directory.lower()
        path = path.lower()
    if len(directory) >= len(path):
        return False
    return path.startswith(
        "%s%s" % (directory, "" if directory.endswith(os.sep) else os.sep)
    )


class API:
    __slots__ = ("database",)

    def __init__(self, database: ExtendedDatabase):
        self.database = database

    @fsigned
    def nb(self, query: str) -> int:
        if query == "entries":
            return len(self.database.query())
        if query == "discarded":
            return len(self.database.get_videos("discarded"))
        return len(self.database.get_videos(*query.strip().split()))

    @fsigned
    def nb_pages(self, query: str, page_size: int) -> int:
        if page_size <= 0:
            raise other.toolsaurus.application.exceptions.InvalidPageSize(page_size)
        count = self.nb(query)
        return (count // page_size) + bool(count % page_size)

    @fsigned
    def valid_size(self) -> FileSize:
        return FileSize(
            sum(video.file_size for video in self.database.get_valid_videos())
        )

    @fsigned
    def valid_length(self) -> Duration:
        return Duration(
            sum(video.raw_microseconds for video in self.database.get_valid_videos())
        )

    @fsigned
    def clear_not_found(self):
        self.database.remove_videos_not_found()

    @fsigned
    def info(self, video_id: int) -> str:
        return self.database.get_video_string(video_id)

    @fsigned
    def download_image(self, video_id: int) -> str:
        return ImageUtils.thumbnail_to_base64(
            str(self.database.get_video_field(video_id, "thumbnail_path"))
        )

    @fsigned
    def download_image_from_filename(self, filename: str) -> str:
        return ImageUtils.thumbnail_to_base64(
            str(self.database.get_video_from_filename(filename).thumbnail_path)
        )

    @fsigned
    def open_image(self, video_id: int):
        return self.database.get_video_field(video_id, "thumbnail_path").open()

    @fsigned
    def open_image_from_filename(self, filename: str):
        return self.database.get_video_from_filename(filename).thumbnail_path.open()

    @fsigned
    def clip(self, video_id: int, start: int, length: int) -> str:
        return VideoClipping.video_clip_to_base64(
            path=self.database.get_video_filename(video_id),
            time_start=start,
            clip_seconds=length,
            unique_id=self.database.get_video_field(video_id, "thumb_name"),
        )

    @fsigned
    def clip_from_filename(self, filename: str, start: int, length: int) -> str:
        return self.clip(self.database.get_video_id(filename), start, length)

    @fsigned
    def open(self, video_id: int) -> AbsolutePath:
        return self.database.get_video_filename(video_id).open()

    @fsigned
    def images(self, indices: str):
        videos = []
        errors = []
        unknown = []
        for piece in indices.strip().split():
            if piece:
                try:
                    video_id = int(piece)
                except ValueError:
                    errors.append(piece)
                else:
                    if self.database.has_video_id(video_id):
                        videos.append(
                            self.database.get_video_fields(
                                video_id, ("filename", "thumbnail_path")
                            )
                        )
                    else:
                        unknown.append(video_id)
        temp_file_path = None
        if videos:
            file_content = """<html><body>%s</body></html>""" % (
                "".join(
                    f"<div><div>"
                    f'<img alt="{v.filename}" src="file://{v.thumbnail_path}"/>'
                    f"</div><div><strong>{v.filename}</strong>"
                    f"</div></div>"
                    for v in videos
                )
            )
            temp_file_path = generate_temp_file_path("html")
            with open(temp_file_path.path, "w") as file:
                file.write(file_content)
            temp_file_path.open()
        with StringPrinter() as printer:
            if videos:
                printer.title("Images:")
                for video in videos:
                    printer.write(video.filename)
            if errors:
                printer.title("Invalid:")
                for error in errors:
                    printer.write(error)
            if unknown:
                printer.title("Unknown:")
                for value in unknown:
                    printer.write(value)
            if temp_file_path:
                printer.write("Output:", temp_file_path)
            return str(printer)

    @fsigned
    def playlist(self, indices: str) -> str:
        videos = []
        errors = []
        unknown = []
        for piece in indices.strip().split():
            if piece:
                try:
                    video_id = int(piece)
                except ValueError:
                    errors.append(piece)
                else:
                    if self.database.has_video_id(video_id):
                        videos.append(
                            self.database.get_video_fields(video_id, ["filename"])
                        )
                    else:
                        unknown.append(video_id)
        temp_file_path = None
        if videos:
            tracks = "".join(
                "<track><location>%s</location></track>" % video.filename.uri
                for video in videos
            )
            file_content = (
                f'<?xml version="1.0" encoding="UTF-8"?>'
                f'<playlist version="1" xmlns="http://xspf.org/ns/0/">'
                f"<trackList>{tracks}</trackList>"
                f"</playlist>"
            )
            temp_file_path = generate_temp_file_path("xspf")
            with open(temp_file_path.path, "w") as file:
                file.write(file_content)
            temp_file_path.open()
        with StringPrinter() as printer:
            if videos:
                printer.title("Playlist:")
                for video in videos:
                    printer.write(video.filename)
            if errors:
                printer.title("Invalid:")
                for error in errors:
                    printer.write(error)
            if unknown:
                printer.title("Unknown:")
                for value in unknown:
                    printer.write(value)
            if temp_file_path:
                printer.write("Output:", temp_file_path)
            return str(printer)

    @fsigned
    def open_from_filename(self, filename: str) -> AbsolutePath:
        return self.database.get_video_from_filename(filename).filename.open()

    @fsigned
    def delete(self, video_id: int) -> AbsolutePath:
        return self.database.delete_video(video_id)

    @fsigned
    def delete_unreadable(self, video_id: int):
        return self.database.delete_video(video_id)

    @fsigned
    def delete_unreadable_from_filename(self, filename: str):
        return self.database.delete_video(
            self.database.get_unreadable_from_filename(filename).video_id
        )

    @fsigned
    def delete_from_filename(self, filename: str) -> AbsolutePath:
        return self.database.delete_video(
            self.database.get_video_from_filename(filename).video_id
        )

    @fsigned
    def rename(self, video_id: int, new_title: str) -> int:
        if new_title is None or not str(new_title):
            raise other.toolsaurus.application.exceptions.MissingVideoNewTitle()
        self.database.change_video_file_title(video_id, str(new_title))
        return video_id

    @fsigned
    def rename_from_filename(self, filename: str, new_title: str) -> (str, str):
        if new_title is None or not str(new_title):
            raise other.toolsaurus.application.exceptions.MissingVideoNewTitle()
        video = self.database.get_video_from_filename(filename)  # type: Video
        self.database.change_video_file_title(video.video_id, str(new_title))
        return video.filename.path, video.filename.file_title

    @fsigned
    def same_sizes(self) -> Dict[int, List[Video]]:
        sizes = {}
        for video in self.database.get_valid_videos():
            sizes.setdefault(video.size, []).append(video)
        return {
            size: elements for (size, elements) in sizes.items() if len(elements) > 1
        }

    @fsigned
    def find(self, terms: str) -> List[Video]:
        return sorted(
            VideoFeatures.find(
                SearchDef(terms, "and"), self.database.get_valid_videos()
            ),
            key=lambda video: video.date,
            reverse=True,
        )

    @fsigned
    def find_batch(self, path: str) -> List[Tuple[str, List[Video]]]:
        results = []
        for sentence in other.toolsaurus.database.database.load_list_file(path):
            results.append((sentence, self.find(sentence)))
        return results

    @fsigned
    def list(self, fields: str, page_size: int, page_number: int) -> List[Video]:
        if page_size <= 0:
            raise other.toolsaurus.application.exceptions.InvalidPageSize(page_size)
        if page_number < 0:
            raise other.toolsaurus.application.exceptions.InvalidPageNumber(page_number)
        sorting = VideoSorting(fields)
        videos = sorted(
            self.database.get_valid_videos(),
            key=lambda video: video.to_comparable(sorting),
        )
        return videos[(page_size * page_number) : (page_size * (page_number + 1))]

    @fsigned
    def videos(self) -> List[Video]:
        return self.database.get_valid_videos()

    @fsigned
    def not_found(self):
        return sorted(
            self.database.get_videos("readable", "not_found"),
            key=lambda video: video.filename,
        )

    @fsigned
    def not_found_html(self):
        videos = self.not_found()
        if not videos:
            return
        count = len(videos)
        size = FileSize(sum(video.file_size for video in videos))
        length = Duration(sum(video.length.total_microseconds for video in videos))
        file_content = """
        <html>
        <head>
            <style>
                table {margin: auto;}
                .duration {color: red;}
                .video_id {color: rgb(130, 130, 130);}
                h1, h2, h3 {text-align: center;}
            </style>
        </head>
        <body>
        <h1>%(count)s video(s)</h1>
        <h2>Total size: %(size)s</h2>
        <h3>Total length: %(length)s</h3>
        <table><tbody>%(body)s</tbody></table>
        </body>
        </html>
        """ % {
            "count": count,
            "size": size,
            "length": length,
            "body": "".join(
                """
                <tr>
                    <td><img alt="%(alt)s" src="file://%(src)s"/></td>
                    <td>
                        <div><code class="video_id">%(video_id)s</code></div>
                        <div><strong><u>%(meta_title)s</u></strong></div>
                        <div><strong><em/>%(file_title)s</em></strong></div>
                        <div><code>%(filename)s</code></div>
                        <div>
                            <strong><code>%(size)s</code></strong> | 
                            <strong class="duration">%(duration)s</strong>
                        </div>
                    </td>
                </tr>
                """
                % {
                    "video_id": video.video_id,
                    "alt": video.filename,
                    "src": video.thumbnail_path,
                    "filename": video.filename,
                    "meta_title": video.meta_title,
                    "file_title": video.file_title,
                    "size": video.size,
                    "duration": video.length,
                }
                for video in videos
            ),
        }
        temp_file_path = generate_temp_file_path("html")
        with open(temp_file_path.path, "w", encoding="utf-8") as file:
            file.write(file_content)
        temp_file_path.open()
        return str(temp_file_path)

    @fsigned
    def not_found_from_folder(self, folder: str):
        folder = AbsolutePath.ensure(folder)
        if not folder.isdir():
            return ""
        videos = []
        for video in self.database.get_videos("readable", "not_found"):
            if path_in_directory(
                video.filename,
                folder,
                is_case_insensitive=self.database.sys_is_case_insensitive,
            ):
                videos.append(video)
        videos.sort(key=lambda v: v.filename)
        return videos

    @fsigned
    def delete_not_found_from_folder(self, folder: str):
        for video in self.not_found_from_folder(folder):
            self.delete(video.video_id)

    @fsigned
    def unreadable(self):
        return sorted(
            self.database.get_videos("unreadable", "found"),
            key=lambda video: video.filename,
        )

    @fsigned
    def missing_thumbnails(self):
        return sorted(
            self.database.get_videos("readable", "found", "without_thumbnails"),
            key=lambda video: video.filename,
        )

    @fdef(other.toolsaurus.functions.bool_type)
    def update(self, ensure_miniatures=False):
        self.database.refresh(ensure_miniatures)

    @fsigned
    def list_files(self, output: str):
        self.database.list_files(output)
        output_path = AbsolutePath(output)
        if not output_path.isfile():
            raise OSError("Unable to output videos file names in %s" % output_path)
        return str(output_path)

    @fsigned
    def field_names(self):
        return functions.class_get_public_attributes(Video, ("errors", "properties"))


class ConsoleParser(FunctionParser):
    __slots__ = ("api",)

    def __init__(self, list_file_path):
        super(ConsoleParser, self).__init__()
        # Load API.
        self.api = API(
            ExtendedDatabase.load_from_list_file_path(list_file_path, update=False)
        )
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


def main():
    command_line_interface(ConsoleParser(TEST_LIST_FILE_PATH))


if __name__ == "__main__":
    main()
