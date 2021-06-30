import functools
import tempfile
from typing import Dict, List, Tuple, Union

from pysaurus.core import exceptions, functions
from pysaurus.core.classes import Enumeration, StringPrinter
from pysaurus.core.components import AbsolutePath, Duration, FilePath, FileSize
from pysaurus.core.database import path_utils
from pysaurus.core.database.database import Database
from pysaurus.core.database.video import VIDEO_UNIQUE_FIELDS, Video
from pysaurus.core.database.video_features import VideoFeatures
from pysaurus.core.database.video_state import VideoState
from pysaurus.core.function_parser import FunctionParser

TEMP_DIR = tempfile.gettempdir()
TEMP_PREFIX = tempfile.gettempprefix() + "_pysaurus_"

FieldType = Enumeration(VIDEO_UNIQUE_FIELDS)


def generate_temp_file_path(extension):
    temp_file_id = 0
    while True:
        temp_file_path = FilePath(
            TEMP_DIR, "%s%s" % (TEMP_PREFIX, temp_file_id), extension
        )
        if temp_file_path.exists():
            temp_file_id += 1
        else:
            break
    return temp_file_path


def compare_videos(v1: Video, v2: Video, sorting: List[Tuple[str, bool]]):
    for field, reverse in sorting:
        f1 = getattr(v1, field)
        f2 = getattr(v2, field)
        ret = 0
        if f1 < f2:
            ret = -1
        elif f2 < f1:
            ret = 1
        if ret:
            return -ret if reverse else ret
    return 0


def parse_fields(fields: str):
    real_fields = []
    pieces = fields.split()
    for piece in pieces:
        if piece[0] in "-+":
            piece = piece[1:]
        real_fields.append(FieldType(piece))
    return real_fields


class API:
    __slots__ = ("database",)

    def __init__(self, database: Database):
        self.database = database

    def export_api(self, function_parser):
        # type: (FunctionParser) -> None
        function_parser.add(self.clear_not_found)
        function_parser.add(
            self.clip, arguments={"video_id": int, "start": int, "length": int}
        )
        function_parser.add(
            self.clip_from_filename,
            arguments={"filename": str, "start": int, "length": int},
        )
        function_parser.add(self.delete, arguments={"video_id": int})
        function_parser.add(self.delete_from_filename, arguments={"filename": str})
        function_parser.add(
            self.delete_not_found_from_folder, arguments={"folder": str}
        )
        function_parser.add(self.delete_unreadable, arguments={"video_id": int})
        function_parser.add(
            self.delete_unreadable_from_filename, arguments={"filename": str}
        )
        function_parser.add(self.download_image, arguments={"video_id": int})
        function_parser.add(
            self.download_image_from_filename, arguments={"filename": str}
        )
        function_parser.add(self.field_names)
        function_parser.add(self.find, arguments={"terms": str})
        function_parser.add(self.find_batch, arguments={"path": str})
        function_parser.add(self.images, arguments={"indices": str})
        function_parser.add(self.info, arguments={"video_id": int})
        function_parser.add(
            self.list, arguments={"fields": str, "page_size": int, "page_number": int}
        )
        function_parser.add(self.list_files, arguments={"output": str})
        function_parser.add(self.missing_thumbnails)
        function_parser.add(self.nb, arguments={"query": str})
        function_parser.add(self.nb_pages, arguments={"query": str, "page_size": int})
        function_parser.add(self.not_found)
        function_parser.add(self.not_found_html)
        function_parser.add(self.not_found_from_folder, arguments={"folder": str})
        function_parser.add(self.open, arguments={"video_id": int})
        function_parser.add(self.open_from_filename, arguments={"filename": str})
        function_parser.add(self.open_image, arguments={"video_id": int})
        function_parser.add(self.open_image_from_filename, arguments={"filename": str})
        function_parser.add(self.playlist, arguments={"indices": str})
        function_parser.add(self.rename, arguments={"video_id": int, "new_title": str})
        function_parser.add(
            self.rename_from_filename, arguments={"filename": str, "new_title": str}
        )
        function_parser.add(self.same_sizes)
        function_parser.add(self.unreadable)
        function_parser.add(
            self.update, arguments={"ensure_miniatures": functions.bool_type}
        )
        function_parser.add(self.valid_length)
        function_parser.add(self.valid_size)
        function_parser.add(self.videos)

    # ------------------------------------------------------------------------------------------------------------------

    def nb(self, query):
        # type: (str) -> int
        if query == "entries":
            return self.database.nb_entries
        if query == "discarded":
            return self.database.nb_discarded
        return len(self.database.get_videos(*query.strip().split()))

    def nb_pages(self, query, page_size):
        # type: (str, int) -> int
        if page_size <= 0:
            raise exceptions.InvalidPageSize(page_size)
        count = self.nb(query)
        return (count // page_size) + bool(count % page_size)

    def valid_size(self):
        # type: () -> FileSize
        return FileSize(
            sum(video.file_size for video in self.database.get_valid_videos())
        )

    def valid_length(self):
        # type: () -> Duration
        return Duration(
            sum(video.raw_microseconds for video in self.database.get_valid_videos())
        )

    def clear_not_found(self):
        # type: () -> None
        self.database.remove_videos_not_found()

    def info(self, video_id):
        # type: (int) -> Union[Video, VideoState]
        return self.database.get_video_from_id(
            video_id, required=False
        ) or self.database.get_unreadable_from_id(video_id, required=False)

    def download_image(self, video_id):
        # type: (int) -> str
        return VideoFeatures.thumbnail_to_base64(
            self.database.get_video_from_id(video_id)
        )

    def download_image_from_filename(self, filename):
        # type: (str) -> str
        return VideoFeatures.thumbnail_to_base64(
            self.database.get_video_from_filename(filename)
        )

    def open_image(self, video_id):
        return self.database.get_video_from_id(video_id).thumbnail_path.open()

    def open_image_from_filename(self, filename):
        return self.database.get_video_from_filename(filename).thumbnail_path.open()

    def clip(self, video_id, start, length):
        # type: (int, int, int) -> str
        return VideoFeatures.clip_to_base64(
            self.database.get_video_from_id(video_id), start, length
        )

    def clip_from_filename(self, filename, start, length):
        # type: (str, int, int) -> str
        return VideoFeatures.clip_to_base64(
            self.database.get_video_from_filename(filename), start, length
        )

    def open(self, video_id):
        # type: (int) -> AbsolutePath
        return self.database.get_video_from_id(video_id).filename.open()

    def images(self, indices):
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
                    video = self.database.get_video_from_id(video_id, required=False)
                    if video:
                        videos.append(video)
                    else:
                        unknown.append(video_id)
        temp_file_path = None
        if videos:
            file_content = """<html><body>%s</body></html>""" % (
                "".join(
                    '<div><div><img alt="%s" src="file://%s"/></div><div><strong>%s</strong></div></div>'
                    % (video.filename, video.thumbnail_path, video.filename)
                    for video in videos
                )
            )
            temp_file_id = 0
            while True:
                temp_file_path = FilePath(
                    TEMP_DIR, "%s%s" % (TEMP_PREFIX, temp_file_id), "html"
                )
                if temp_file_path.exists():
                    temp_file_id += 1
                else:
                    break
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

    def playlist(self, indices):
        # type: (str) -> str
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
                    video = self.database.get_video_from_id(video_id, required=False)
                    if video:
                        videos.append(video)
                    else:
                        unknown.append(video_id)
        temp_file_path = None
        if videos:
            tracks = "".join(
                "<track><location>%s</location></track>" % video.filename.uri
                for video in videos
            )
            file_content = (
                """<?xml version="1.0" encoding="UTF-8"?><playlist version="1" xmlns="http://xspf.org/ns/0/"><trackList>%s</trackList></playlist>"""
                % tracks
            )
            temp_file_id = 0
            while True:
                temp_file_path = FilePath(
                    TEMP_DIR, "%s%s" % (TEMP_PREFIX, temp_file_id), "xspf"
                )
                if temp_file_path.exists():
                    temp_file_id += 1
                else:
                    break
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

    def open_from_filename(self, filename):
        # type: (str) -> AbsolutePath
        return self.database.get_video_from_filename(filename).filename.open()

    def delete(self, video_id):
        # type: (int) -> AbsolutePath
        return self.database.delete_video(self.database.get_video_from_id(video_id))

    def delete_unreadable(self, video_id):
        return self.database.delete_video(
            self.database.get_unreadable_from_id(video_id)
        )

    def delete_unreadable_from_filename(self, filename):
        return self.database.delete_video(
            self.database.get_unreadable_from_filename(filename)
        )

    def delete_from_filename(self, filename):
        # type: (str) -> AbsolutePath
        return self.database.delete_video(
            self.database.get_video_from_filename(filename)
        )

    def rename(self, video_id, new_title):
        # type: (int, str) -> int
        if new_title is None or not str(new_title):
            raise exceptions.MissingVideoNewTitle()
        video = self.database.get_video_from_id(video_id)  # type: Video
        self.database.change_video_file_title(video, str(new_title))
        return video.video_id

    def rename_from_filename(self, filename, new_title):
        # type: (str, str) -> (str, str)
        if new_title is None or not str(new_title):
            raise exceptions.MissingVideoNewTitle()
        video = self.database.get_video_from_filename(filename)  # type: Video
        self.database.change_video_file_title(video, str(new_title))
        return video.filename.path, video.filename.title

    def same_sizes(self):
        # type: () -> Dict[int, List[Video]]
        sizes = {}
        for video in self.database.get_valid_videos():
            sizes.setdefault(video.size, []).append(video)
        return {
            size: elements for (size, elements) in sizes.items() if len(elements) > 1
        }

    def find(self, terms):
        # type: (str) -> List[Video]
        terms = functions.string_to_pieces(terms)
        return [
            video
            for video in self.database.get_valid_videos()
            if all(
                term in video.title.lower() or term in video.filename.path.lower()
                for term in terms
            )
        ]

    def find_batch(self, path):
        # type: (str) -> List[Tuple[str, List[Video]]]
        results = []
        for sentence in path_utils.load_list_file(path):
            results.append((sentence, self.find(sentence)))
        return results

    def list(self, fields, page_size, page_number):
        # type: (str, int, int) -> List[Video]
        if page_size <= 0:
            raise exceptions.InvalidPageSize(page_size)
        sorting = []
        pieces = fields.split()
        for piece in pieces:
            if piece[0] in "-+":
                reverse = piece[0] == "-"
                piece = piece[1:]
            else:
                reverse = False
            field = FieldType(piece)
            sorting.append((field, reverse))
        videos = sorted(
            self.database.get_valid_videos(),
            key=functools.cmp_to_key(lambda v1, v2: compare_videos(v1, v2, sorting)),
        )
        return videos[(page_size * page_number) : (page_size * (page_number + 1))]

    def videos(self):
        # type: () -> List[Video]
        return self.database.get_valid_videos()

    def not_found(self):
        return sorted(
            self.database.get_videos("readable", "not_found"),
            key=lambda video: video.filename,
        )

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
                        <div><strong><code>%(size)s</code></strong> | <strong class="duration">%(duration)s</strong></div>
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

    def not_found_from_folder(self, folder):
        folder = AbsolutePath.ensure(folder)
        if not folder.isdir():
            return ""
        videos = []
        for video in self.database.get_videos("readable", "not_found"):
            if video.filename.in_directory(
                folder, is_case_insensitive=self.database.sys_is_case_insensitive
            ):
                videos.append(video)
        videos.sort(key=lambda video: video.filename)
        return videos

    def delete_not_found_from_folder(self, folder):
        for video in self.not_found_from_folder(folder):
            self.delete(video.video_id)

    def unreadable(self):
        return sorted(
            self.database.get_videos("unreadable", "found"),
            key=lambda video: video.filename,
        )

    def missing_thumbnails(self):
        return sorted(
            self.database.get_videos("readable", "found", "without_thumbnails"),
            key=lambda video: video.filename,
        )

    def update(self, ensure_miniatures=False):
        self.database.refresh(ensure_miniatures)

    def list_files(self, output):
        self.database.list_files(output)
        output_path = AbsolutePath(output)
        if not output_path.isfile():
            raise OSError("Unable to output videos file names in %s" % output_path)
        return str(output_path)

    def field_names(self):
        return list(VIDEO_UNIQUE_FIELDS)
