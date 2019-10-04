from pysaurus.core.classes import StringPrinter, Table
from pysaurus.core.components import FileSize
from pysaurus.core.database.api import API
from pysaurus.core.function_parsing.function_parser import FunctionParser


class ConsoleParser(FunctionParser):
    __slots__ = 'api',

    def __init__(self, list_file_path):
        super(ConsoleParser, self).__init__()
        # Load API.
        self.api = API(list_file_path)
        # Update parser from API.
        self.api.export_api(self)
        # Update parser with wrapped functions.
        self.override_definition(self.find)
        self.override_definition(self.find_batch)
        self.override_definition(self.list)
        self.override_definition(self.missing_thumbnails)
        self.override_definition(self.not_found)
        self.override_definition(self.same_sizes)
        self.override_definition(self.unreadable)
        self.remove_definition(self.api.clip)
        self.remove_definition(self.api.clip_from_filename)
        self.remove_definition(self.api.download_image)
        self.remove_definition(self.api.download_image_from_filename)
        self.remove_definition(self.api.videos)

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
                    video.size,
                    video.filename
                ])
            return Table(headers=headers, lines=lines)

    def find_batch(self, path):
        batch_results = self.api.find_batch(path)
        headers = ['', 'Date modified', 'ID', 'Size', 'Path']
        with StringPrinter() as printer:
            for sentence, found in batch_results:
                printer.write(sentence)
                if found:
                    lines = []
                    for video in found:
                        lines.append(['',
                                      video.filename.get_date_modified(),
                                      video.video_id,
                                      video.size,
                                      video.filename])
                    printer.write(Table(headers, lines))
                else:
                    printer.write('\t(nothing)')
            return str(printer)

    def list(self, field, reverse, page_size, page_number):
        selected_videos = self.api.list(field, reverse, page_size, page_number)
        headers = ['ID', field.upper(), 'Path']
        lines = []
        for i, video in enumerate(selected_videos):
            lines.append([video.video_id, video.get(field), video.filename])
        return Table(headers=headers, lines=lines)

    def missing_thumbnails(self):
        headers = ['ID', 'Size', 'Filename']
        lines = [[video.video_id, FileSize(video.filename.get_size()), video.filename]
                 for video in self.api.missing_thumbnails()]
        return Table(headers, lines)

    def not_found(self):
        headers = ['ID', 'Filename']
        lines = [[video.video_id, video.filename] for video in self.api.not_found()]
        return Table(headers, lines)

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

    def unreadable(self):
        headers = ['ID', 'Size', 'Filename']
        lines = [[video.video_id, FileSize(video.filename.get_size()), video.filename]
                 for video in self.api.unreadable()]
        return Table(headers, lines)
