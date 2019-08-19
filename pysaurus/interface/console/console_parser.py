from pysaurus.core.function_parsing.function_parser import FunctionParser
from pysaurus.core.utils.classes import Table
from pysaurus.public.api import API
from pysaurus.core.components.file_size import FileSize


class ConsoleParser(FunctionParser):
    __slots__ = 'api',

    def __init__(self, list_file_path):
        super(ConsoleParser, self).__init__()
        # Load API.
        self.api = API(list_file_path)
        # Update parser from API.
        self.api.export_api(self)
        # Update parser with wrapped functions.
        self.get_definition(self.api.same_sizes).function = self.same_sizes
        self.get_definition(self.api.find).function = self.find
        self.get_definition(self.api.list).function = self.list
        self.get_definition(self.api.not_found).function = self.not_found
        self.get_definition(self.api.unreadable).function = self.unreadable
        self.get_definition(self.api.thumbnail_path).function = self.thumbnail_path
        self.get_definition(self.api.thumbnail_path_from_filename).function = self.thumbnail_path_from_filename
        self.remove_definition(self.api.clip)
        self.remove_definition(self.api.clip_from_filename)
        self.remove_definition(self.api.image)
        self.remove_definition(self.api.image_from_filename)

    def same_sizes(self):
        duplicated_sizes = self.api.same_sizes()
        if duplicated_sizes:
            headers = ['Size', 'ID', 'Path']
            lines = []
            for size in sorted(duplicated_sizes.keys()):
                elements = duplicated_sizes[size]  # type: list
                elements.sort(key=lambda v: v.filename)
                for video in elements:
                    lines.append([size, video.video_id, '"%s"' % video.filename])
                lines.append([])
            return Table(headers=headers, lines=lines)

    def find(self, terms):
        found = self.api.find(terms)
        if found:
            found.sort(key=lambda v: v.filename.get_date_modified().time, reverse=True)
            headers = ['Date modified', 'ID', 'Size', 'Path']
            lines = []
            for video in found:
                lines.append([
                    video.filename.get_date_modified(),
                    video.video_id,
                    video.get_size(),
                    video.filename
                ])
            return Table(headers=headers, lines=lines)

    def list(self, field, reverse, page_size, page_number):
        selected_videos = self.api.list(field, reverse, page_size, page_number)
        headers = ['No', 'ID', field.upper(), 'Path']
        lines = []
        for i, video in enumerate(selected_videos):
            lines.append(['(%d)' % i, video.video_id, video.get(field), video.filename])
        return Table(headers=headers, lines=lines)

    def not_found(self):
        headers = ['ID', 'Filename']
        lines = [[video.video_id, video.filename] for video in self.api.not_found()]
        return Table(headers, lines)

    def unreadable(self):
        headers = ['Size', 'Filename']
        lines = [[FileSize(video.filename.get_size()), video.filename] for video in self.api.unreadable()]
        return Table(headers, lines)

    def thumbnail_path(self, video_id):
        return self.api.thumbnail_path(video_id).open()

    def thumbnail_path_from_filename(self, filename):
        return self.api.thumbnail_path_from_filename(filename).open()
