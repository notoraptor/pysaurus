from pysaurus.core.function_parsing.function_parser import FunctionParser
from pysaurus.core.utils.classes import Table
from pysaurus.public.api import API


class ConsoleParser(FunctionParser):
    __slots__ = 'api',

    def __init__(self):
        super(ConsoleParser, self).__init__()
        # Load API.
        self.api = API()
        # Update parser from API.
        self.api.export_api(self)
        # Update parser with wrapped functions.
        self.get_definition(self.api.same_sizes).function = self.same_sizes
        self.get_definition(self.api.find).function = self.find
        self.get_definition(self.api.list).function = self.list

    def same_sizes(self):
        duplicated_sizes = self.api.same_sizes()
        if duplicated_sizes:
            headers = ['Size', 'ID', 'Path']
            lines = []
            for size in sorted(duplicated_sizes.keys()):
                elements = duplicated_sizes[size]  # type: list
                elements.sort(key=lambda v: v.filename)
                for video in elements:
                    lines.append([size, self.api.database.get_video_id(video), '"%s"' % video.filename])
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
                    self.api.database.get_video_id(video),
                    video.get_size(),
                    video.filename
                ])
            return Table(headers=headers, lines=lines)

    def list(self, field, reverse, page_size, page_number):
        selected_videos = self.api.list(field, reverse, page_size, page_number)
        headers = ['No', 'ID', field.upper(), 'Path']
        lines = []
        for i, video in enumerate(selected_videos):
            lines.append(['(%d)' % i, self.api.database.get_video_id(video), video.get(field), video.filename])
        return Table(headers=headers, lines=lines)
