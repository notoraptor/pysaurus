"""
pip install PySciter
"""
import threading
from typing import Optional

import sciter

from pysaurus.core.database.api import API
from pysaurus.core.notification import Notifier, Notification
from pysaurus.core.functions import launch_thread
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH
from pysaurus.core.components import FileSize, Duration


class DatabaseReady(Notification):
    __slots__ = ()


class Frame(sciter.Window):
    def __init__(self):
        super().__init__(ismain=True, uni_theme=True)
        notifier = Notifier()
        notifier.set_default_manager(self._notify)
        self.api = None
        self.notifier = notifier
        self.thread = None  # type: Optional[threading.Thread]
        self.load_file('web/index.html')
        self.expand()

    def _notify(self, notification):
        # type: (Notification) -> None
        print(notification)
        self.call_function('Notifications.notify', {
            'name': notification.get_name(),
            'notification': notification.to_dict(),
            'message': str(notification)
        })

    def _load_database(self):
        self.api = API(TEST_LIST_FILE_PATH,
                       notifier=self.notifier,
                       ensure_miniatures=False,
                       reset=False)
        self.videos = self.api.list('title', self.api.nb('valid'), 0)
        assert len(self.videos) == self.api.database.nb_valid
        self.notifier.notify(DatabaseReady())

    @sciter.script
    def load_database(self):
        self.thread = launch_thread(self._load_database)

    @sciter.script
    def get_video_field_names(self):
        return self.api.field_names()

    @sciter.script
    def count_videos(self):
        return len(self.videos)

    @sciter.script
    def valid_size(self):
        return str(FileSize(sum(video.file_size for video in self.videos)))

    @sciter.script
    def valid_length(self):
        return str(Duration(sum(video.length.total_microseconds for video in self.videos)))

    @sciter.script
    def count_pages(self, page_size):
        assert page_size > 0
        count = len(self.videos)
        return (count // page_size) + bool(count % page_size)

    @sciter.script
    def get_videos_index_range(self, page_size, page_number):
        start = page_size * page_number
        end = min(start + page_size, len(self.videos))
        return start, end

    @sciter.script
    def get_video_field(self, index, field):
        value = getattr(self.videos[index], field)
        return value if isinstance(value, (str, int, float, bool)) else str(value)

    @sciter.script
    def open_video(self, index):
        self.api.open(self.videos[index].video_id)


def main():
    frame = Frame()
    frame.run_app()
    print('End')


if __name__ == '__main__':
    main()
