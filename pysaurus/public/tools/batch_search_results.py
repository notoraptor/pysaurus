from pysaurus.core.utils.classes import StringPrinter, Table


class BatchSearchResults:
    def __init__(self):
        self.results = []

    def __repr__(self):
        return str(self)

    def __str__(self):
        printer = StringPrinter()
        headers = ['', 'Date modified', 'ID', 'Size', 'Path']
        for sentence, found in self.results:
            printer.write(sentence)
            if found:
                lines = []
                for video in found:
                    lines.append([
                        '',
                        video.filename.get_date_modified(),
                        video.video_id,
                        video.get_size(),
                        video.filename
                    ])
                printer.write(Table(headers, lines))
            else:
                printer.write('\t(nothing)')
        return str(printer)