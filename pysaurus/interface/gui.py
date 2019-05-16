import os

import PySimpleGUI as sg

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.database import Database
from pysaurus.core.video import Video

TITLE = 'title'
FILENAME = 'filename'
FORMAT = 'format'
AUDIO_CODEC = 'audio_codec'
VIDEO_CODEC = 'video_codec'
WIDTH = 'width'
HEIGHT = 'height'
FRAME_RATE = 'frame_rate'
SAMPLE_RATE = 'sample_rate'
DURATION = 'duration'
SIZE = 'size'
BIT_RATE = 'bit_rate'
ERRORS = 'errors'


class VideoToDatabase:
    headers = (
        TITLE, FILENAME, FORMAT, AUDIO_CODEC, VIDEO_CODEC, WIDTH, HEIGHT, FRAME_RATE, SAMPLE_RATE, DURATION, SIZE,
        BIT_RATE,
        ERRORS)
    header_titles = {
        TITLE: 'Title',
        FILENAME: 'Path',
        FORMAT: 'Format',
        AUDIO_CODEC: 'Audio codec',
        VIDEO_CODEC: 'Video codec',
        WIDTH: 'Width',
        HEIGHT: 'Height',
        FRAME_RATE: 'Frame rate',
        SAMPLE_RATE: 'Sample rate',
        DURATION: 'Duration',
        SIZE: 'Size',
        BIT_RATE: 'Bit rate',
        ERRORS: 'Error(s)',
    }

    def __init__(self, video: Video):
        self.video = video

    def to_array(self):
        return [getattr(self, header) for header in self.headers]

    @property
    def title(self): return self.video.get_title()

    @property
    def filename(self): return self.video.filename.path

    @property
    def format(self): return self.video.container_format

    @property
    def audio_codec(self): return self.video.audio_codec

    @property
    def video_codec(self): return self.video.video_codec

    @property
    def width(self): return self.video.width

    @property
    def height(self): return self.video.height

    @property
    def frame_rate(self):
        return round(self.video.frame_rate_num / self.video.frame_rate_den)

    @property
    def sample_rate(self): return self.video.sample_rate

    @property
    def duration(self): return self.video.get_duration()

    @property
    def size(self): return self.video.get_size()

    @property
    def bit_rate(self): return self.video.bit_rate

    @property
    def errors(self): return ', '.join(sorted(self.video.errors))


def test_database():
    list_file_path = AbsolutePath(os.path.join('..', '..', '..', '.local', 'test_folder.log'))
    database = Database.load_from_list_file(list_file_path)
    table_headers = [VideoToDatabase.header_titles[header] for header in VideoToDatabase.headers]
    video_entries = [VideoToDatabase(video) for video in database.videos.values()]
    table_values = [[str(e) for e in video_entry.to_array()] for video_entry in video_entries]

    layout = [
        [
            sg.Table(
                vertical_scroll_only=False,
                enable_events=True,
                key='__videos__',
                justification='left',
                auto_size_columns=False,
                size=(None, 30),
                headings=table_headers,
                values=table_values),
            sg.Column(
                [[sg.Image(key='__image__', filename=os.path.join(os.path.dirname(__file__), '..', 'resource', 'default.png'))],
                 [sg.Text('', background_color='gray', auto_size_text=True, key='__title__')]
                ]
            )
        ]
    ]

    window = sg.Window('Window Title', layout, resizable=True)
    image = window.Element('__image__')
    label_title = window.Element('__title__')
    assert image
    assert label_title

    while True:
        event, value = window.Read()
        print(event, value)
        if event is None:
            print(event, "exiting")
            break
        if event == '__videos__' and value['__videos__']:
            selected_row_number = value['__videos__'][0]
            if selected_row_number < len(table_values):
                video_entry = video_entries[selected_row_number]
                label_title.Update(value=video_entry.title)
                thumbnail_path = video_entry.video.get_thumbnail_path(database.database_path)
                if thumbnail_path.isfile():
                    image.Update(filename=thumbnail_path.path)


if __name__ == '__main__':
    test_database()
