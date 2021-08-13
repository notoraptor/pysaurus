from typing import Dict, List, Tuple, Union

from pysaurus.core import exceptions, functions
from pysaurus.core.classes import StringPrinter
from pysaurus.core.components import AbsolutePath, Duration, FileSize
from pysaurus.core.database import path_utils
from pysaurus.core.database.database import Database
from pysaurus.core.database.video import Video
from pysaurus.core.database.video_features import VideoFeatures
from pysaurus.core.database.video_sorting import VideoSorting
from pysaurus.core.database.video_state import VideoState
from pysaurus.core.functions import generate_temp_file_path
from pysaurus.interface.console.function_parser import fdef, fsigned


class API:
    __slots__ = ("database",)

    def __init__(self, database: Database):
        self.database = database

    @fsigned
    def nb(self, query: str) -> int:
        if query == "entries":
            return self.database.nb_entries
        if query == "discarded":
            return self.database.nb_discarded
        return len(self.database.get_videos(*query.strip().split()))

    @fsigned
    def nb_pages(self, query: str, page_size: int) -> int:
        if page_size <= 0:
            raise exceptions.InvalidPageSize(page_size)
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
    def info(self, video_id: int) -> Union[Video, VideoState]:
        return self.database.get_video_from_id(
            video_id, required=False
        ) or self.database.get_unreadable_from_id(video_id, required=False)

    @fsigned
    def download_image(self, video_id: int) -> str:
        return VideoFeatures.thumbnail_to_base64(
            self.database.get_video_from_id(video_id)
        )

    @fsigned
    def download_image_from_filename(self, filename: str) -> str:
        return VideoFeatures.thumbnail_to_base64(
            self.database.get_video_from_filename(filename)
        )

    @fsigned
    def open_image(self, video_id: int):
        return self.database.get_video_from_id(video_id).thumbnail_path.open()

    @fsigned
    def open_image_from_filename(self, filename: str):
        return self.database.get_video_from_filename(filename).thumbnail_path.open()

    @fsigned
    def clip(self, video_id: int, start: int, length: int) -> str:
        return VideoFeatures.clip_to_base64(
            self.database.get_video_from_id(video_id), start, length
        )

    @fsigned
    def clip_from_filename(self, filename: str, start: int, length: int) -> str:
        return VideoFeatures.clip_to_base64(
            self.database.get_video_from_filename(filename), start, length
        )

    @fsigned
    def open(self, video_id: int) -> AbsolutePath:
        return self.database.get_video_from_id(video_id).filename.open()

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
                    video = self.database.get_video_from_id(video_id, required=False)
                    if video:
                        videos.append(video)
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
        return self.database.delete_video(self.database.get_video_from_id(video_id))

    @fsigned
    def delete_unreadable(self, video_id: int):
        return self.database.delete_video(
            self.database.get_unreadable_from_id(video_id)
        )

    @fsigned
    def delete_unreadable_from_filename(self, filename: str):
        return self.database.delete_video(
            self.database.get_unreadable_from_filename(filename)
        )

    @fsigned
    def delete_from_filename(self, filename: str) -> AbsolutePath:
        return self.database.delete_video(
            self.database.get_video_from_filename(filename)
        )

    @fsigned
    def rename(self, video_id: int, new_title: str) -> int:
        if new_title is None or not str(new_title):
            raise exceptions.MissingVideoNewTitle()
        video = self.database.get_video_from_id(video_id)  # type: Video
        self.database.change_video_file_title(video, str(new_title))
        return video.video_id

    @fsigned
    def rename_from_filename(self, filename: str, new_title: str) -> (str, str):
        if new_title is None or not str(new_title):
            raise exceptions.MissingVideoNewTitle()
        video = self.database.get_video_from_filename(filename)  # type: Video
        self.database.change_video_file_title(video, str(new_title))
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
            VideoFeatures.find_text(terms, self.database.get_valid_videos()),
            key=lambda video: video.date,
            reverse=True,
        )

    @fsigned
    def find_batch(self, path: str) -> List[Tuple[str, List[Video]]]:
        results = []
        for sentence in path_utils.load_list_file(path):
            results.append((sentence, self.find(sentence)))
        return results

    @fsigned
    def list(self, fields: str, page_size: int, page_number: int) -> List[Video]:
        if page_size <= 0:
            raise exceptions.InvalidPageSize(page_size)
        if page_number < 0:
            raise exceptions.InvalidPageNumber(page_number)
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
            if video.filename.in_directory(
                folder, is_case_insensitive=self.database.sys_is_case_insensitive
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

    @fdef(functions.bool_type)
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
