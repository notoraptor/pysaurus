from pysaurus.core.function_parsing.function_parser import FunctionParser
from pysaurus.core.utils.classes import Table
from pysaurus.core.utils.functions import bool_type
from pysaurus.public.api import NbType, FieldType, API


class ConsoleInterface(FunctionParser):
    __slots__ = 'interface',

    def __init__(self):
        super(ConsoleInterface, self).__init__()
        self.interface = API()
        self.add(self.interface.valid_size)
        self.add(self.interface.valid_length)
        self.add(self.same_sizes)
        self.add(self.find, arguments={'terms': str})
        self.add(self.interface.open, arguments={'video_id': int})
        self.add(self.interface.delete, arguments={'video_id': int})
        self.add(self.interface.info, arguments={'video_id': int})
        self.add(self.interface.clear_not_found)
        self.add(self.interface.nb, arguments={'query': NbType})
        self.add(self.interface.nb_pages, arguments={'query': NbType, 'page_size': int})
        self.add(self.interface.rename, arguments={'video_id': int, 'new_title': str})
        self.add(self.list, arguments={
            'field': FieldType,
            'reverse': bool_type,
            'page_size': int,
            'page_number': int
        })

    def same_sizes(self):
        duplicated_sizes = self.interface.same_sizes()
        if duplicated_sizes:
            headers = ['Size', 'ID', 'Path']
            lines = []
            for size in sorted(duplicated_sizes.keys()):
                elements = duplicated_sizes[size]  # type: list
                elements.sort(key=lambda v: v.filename)
                for video in elements:
                    lines.append([size, self.interface.database.get_video_id(video), video.filename])
                lines.append([])
            return Table(headers=headers, lines=lines)

    def find(self, terms):
        found = self.interface.find(terms)
        if found:
            found.sort(key=lambda v: v.filename.get_date_modified().time, reverse=True)
            headers = ['Date modified', 'ID', 'Size', 'Path']
            lines = []
            for video in found:
                lines.append([
                    video.filename.get_date_modified(),
                    self.interface.database.get_video_id(video),
                    video.get_size(),
                    video.filename
                ])
            return Table(headers=headers, lines=lines)

    def list(self, field, reverse, page_size, page_number):
        selected_videos = self.interface.list(field, reverse, page_size, page_number)
        headers = ['No', 'ID', field.upper(), 'Path']
        lines = []
        for i, video in enumerate(selected_videos):
            lines.append(['(%d)' % i, self.interface.database.get_video_id(video), video.get(field), video.filename])
        return Table(headers=headers, lines=lines)
