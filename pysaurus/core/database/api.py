from typing import Dict, List, Tuple, Union

from pysaurus.core import exceptions, functions as utils
from pysaurus.core.classes import Enumeration, Table, StringPrinter
from pysaurus.core.components import AbsolutePath, Duration, FileSize, FilePath
from pysaurus.core.database import path_utils
from pysaurus.core.database.database import Database
from pysaurus.core.database.video import Video
from pysaurus.core.database.video_state import VideoState
from pysaurus.core.function_parsing.function_parser import FunctionParser
from pysaurus.core.functions import bool_type
from pysaurus.core.notification import Notifier
import tempfile

TEMP_DIR = tempfile.gettempdir()
TEMP_PREFIX = tempfile.gettempprefix() + '_pysaurus_'

NbType = Enumeration(('entries', 'discarded', 'not_found', 'found', 'unreadable', 'valid', 'thumbnails'))
FieldType = Enumeration(Video.ROW_FIELDS)


class API:
    __slots__ = 'database',

    def __init__(self, list_file_path, notifier=None, ensure_miniatures=True):
        # type: (Union[str, AbsolutePath], Notifier, bool) -> None
        paths = path_utils.load_path_list_file(list_file_path)
        database_folder = list_file_path.get_directory()
        self.database = Database(path=database_folder, folders=paths, notifier=notifier)
        self.update(ensure_miniatures)

    def export_api(self, function_parser):
        # type: (FunctionParser) -> None
        function_parser.add(self.clear_not_found)
        function_parser.add(self.clip, arguments={'video_id': int, 'start': int, 'length': int})
        function_parser.add(self.clip_from_filename, arguments={'filename': str, 'start': int, 'length': int})
        function_parser.add(self.delete, arguments={'video_id': int})
        function_parser.add(self.delete_from_filename, arguments={'filename': str})
        function_parser.add(self.delete_unreadable, arguments={'video_id': int})
        function_parser.add(self.delete_unreadable_from_filename, arguments={'filename': str})
        function_parser.add(self.download_image, arguments={'video_id': int})
        function_parser.add(self.download_image_from_filename, arguments={'filename': str})
        function_parser.add(self.find, arguments={'terms': str})
        function_parser.add(self.find_batch, arguments={'path': str})
        function_parser.add(self.info, arguments={'video_id': int})
        function_parser.add(self.list, arguments={'field': FieldType, 'reverse': bool_type, 'page_size': int, 'page_number': int})
        function_parser.add(self.missing_thumbnails)
        function_parser.add(self.nb, arguments={'query': NbType})
        function_parser.add(self.nb_pages, arguments={'query': NbType, 'page_size': int})
        function_parser.add(self.not_found)
        function_parser.add(self.open, arguments={'video_id': int})
        function_parser.add(self.open_from_filename, arguments={'filename': str})
        function_parser.add(self.open_image, arguments={'video_id': int})
        function_parser.add(self.open_image_from_filename, arguments={'filename': str})
        function_parser.add(self.playlist, arguments={'indices': str})
        function_parser.add(self.rename, arguments={'video_id': int, 'new_title': str})
        function_parser.add(self.rename_from_filename, arguments={'filename': str, 'new_title': str})
        function_parser.add(self.reset_thumbnail_errors)
        function_parser.add(self.same_sizes)
        function_parser.add(self.unreadable)
        function_parser.add(self.update, arguments={'ensure_miniatures': bool_type})
        function_parser.add(self.valid_length)
        function_parser.add(self.valid_size)
        function_parser.add(self.videos)

    # ------------------------------------------------------------------------------------------------------------------

    def nb(self, query):
        # type: (str) -> int
        return getattr(self.database, 'nb_%s' % NbType(query))

    def nb_pages(self, query, page_size):
        # type: (str, int) -> int
        if page_size <= 0:
            raise exceptions.InvalidPageSize(page_size)
        count = self.nb(query)
        return (count // page_size) + bool(count % page_size)

    def valid_size(self):
        # type: () -> FileSize
        return FileSize(sum(video.file_size for video in self.database.videos()))

    def valid_length(self):
        # type: () -> Duration
        return Duration(sum(video.length.total_microseconds for video in self.database.videos()))

    def clear_not_found(self):
        # type: () -> None
        self.database.remove_videos_not_found()

    def info(self, video_id):
        # type: (int) -> Union[Video, VideoState]
        return (self.database.get_video_from_id(video_id, required=False)
                or self.database.get_unreadable_from_id(video_id, required=False))

    def download_image(self, video_id):
        # type: (int) -> str
        return self.database.get_video_from_id(video_id).thumbnail_to_base64()

    def download_image_from_filename(self, filename):
        # type: (str) -> str
        return self.database.get_video_from_filename(filename).thumbnail_to_base64()

    def open_image(self, video_id):
        return self.database.get_video_from_id(video_id).get_thumbnail_path().open()

    def open_image_from_filename(self, filename):
        return self.database.get_video_from_filename(filename).get_thumbnail_path().open()

    def clip(self, video_id, start, length):
        # type: (int, int, int) -> str
        return self.database.get_video_from_id(video_id).clip_to_base64(start, length)

    def clip_from_filename(self, filename, start, length):
        # type: (str, int, int) -> str
        return self.database.get_video_from_filename(filename).clip_to_base64(start, length)

    def open(self, video_id):
        # type: (int) -> AbsolutePath
        return self.database.get_video_from_id(video_id).filename.open()

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
            tracks = ''.join('<track><location>%s</location></track>' % video.filename.uri for video in videos)
            file_content = """<?xml version="1.0" encoding="UTF-8"?>
<playlist version="1" xmlns="http://xspf.org/ns/0/"><trackList>%s</trackList></playlist>""" % tracks
            temp_file_id = 0
            while True:
                temp_file_path = FilePath(TEMP_DIR, '%s%s' % (TEMP_PREFIX, temp_file_id), 'xspf')
                if temp_file_path.exists():
                    temp_file_id += 1
                else:
                    break
            with open(temp_file_path.path, 'w') as file:
                file.write(file_content)
            temp_file_path.open()
        with StringPrinter() as printer:
            if videos:
                printer.title('Playlist:')
                for video in videos:
                    printer.write(video.filename)
            if errors:
                printer.title('Invalid:')
                for error in errors:
                    printer.write(error)
            if unknown:
                printer.title('Unknown:')
                for value in unknown:
                    printer.write(value)
            if temp_file_path:
                printer.write('Output:', temp_file_path)
            return str(printer)

    def open_from_filename(self, filename):
        # type: (str) -> AbsolutePath
        return self.database.get_video_from_filename(filename).filename.open()

    def delete(self, video_id):
        # type: (int) -> AbsolutePath
        return self.database.delete_video(self.database.get_video_from_id(video_id))

    def delete_unreadable(self, video_id):
        return self.database.delete_video(self.database.get_unreadable_from_id(video_id))

    def delete_unreadable_from_filename(self, filename):
        return self.database.delete_video(self.database.get_unreadable_from_filename(filename))

    def delete_from_filename(self, filename):
        # type: (str) -> AbsolutePath
        return self.database.delete_video(
            self.database.get_video_from_filename(filename))

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
        for video in self.database.videos():
            sizes.setdefault(video.size, []).append(video)
        return {size: elements for (size, elements) in sizes.items() if len(elements) > 1}

    def find(self, terms):
        # type: (str) -> List[Video]
        terms = utils.string_to_pieces(terms)
        return [video for video in self.database.videos()
                if all(term in video.title.lower() or term in video.filename.path.lower() for term in terms)]

    def find_batch(self, path):
        # type: (str) -> List[Tuple[str, List[Video]]]
        results = []
        for sentence in path_utils.load_list_file(path):
            results.append((sentence, self.find(sentence)))
        return results

    def list(self, field, reverse, page_size, page_number):
        # type: (str, bool, int, int) -> List[Video]
        if page_size <= 0:
            raise exceptions.InvalidPageSize(page_size)
        field = FieldType(field)  # type: str
        reverse = utils.bool_type(reverse)
        videos = sorted(self.database.videos(), key=lambda v: v.get(field), reverse=reverse)
        return videos[(page_size * page_number):(page_size * (page_number + 1))]

    def videos(self):
        # type: () -> Table
        return Table(headers=Video.ROW_FIELDS,
                     lines=[video.to_row() for video in self.database.videos()])

    def not_found(self):
        return sorted(self.database.videos(found=False, not_found=True), key=lambda video: video.filename)

    def unreadable(self):
        return sorted(self.database.videos(valid=False, unreadable=True), key=lambda video: video.filename)

    def missing_thumbnails(self):
        return sorted(self.database.videos(with_thumbs=False, no_thumbs=True),
                      key=lambda video: video.filename)

    def reset_thumbnail_errors(self):
        count = 0
        for video in self.database.videos(with_thumbs=False, no_thumbs=True):
            video.error_thumbnail = False
            count += 1
        if count:
            self.database.save()

    def update(self, ensure_miniatures=False):
        self.reset_thumbnail_errors()
        self.database.update()
        self.database.ensure_thumbnails()
        if ensure_miniatures:
            self.database.ensure_miniatures()
