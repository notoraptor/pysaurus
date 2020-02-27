"""
pip install PySciter
"""
import threading
import multiprocessing
from typing import Optional, List

import sciter
import queue
import time
import traceback
import random

from pysaurus.core import functions
from pysaurus.core.components import FileSize, Duration
from pysaurus.core.database.api import API
from pysaurus.core.database.video import Video
from pysaurus.core.database.notifications import DatabaseReady
from pysaurus.core.functions import launch_thread
from pysaurus.core.notification import Notifier, Notification
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH
from pysaurus.interface.common.parallel_notifier import ParallelNotifier


def filter_exact(video, terms):
    return ' '.join(terms) in ' '.join(video.terms())


def filter_and(video, terms):
    video_terms = video.terms(as_set=True)
    return all(term in video_terms for term in terms)


def filter_or(video, terms):
    video_terms = video.terms(as_set=True)
    return any(term in video_terms for term in terms)


VIDEO_FILTERS = {'exact': filter_exact, 'and': filter_and, 'or': filter_or}

class Frame(sciter.Window):

    def __init__(self):
        super().__init__(ismain=True, uni_theme=True)
        notifier = Notifier()
        notifier.set_default_manager(self._notify)
        self.api = None
        self.multiprocessing_manager = multiprocessing.Manager()
        self.notifier = ParallelNotifier(self.multiprocessing_manager.Queue())
        self.thread = None  # type: Optional[threading.Thread]
        self.videos = []  # type: List[Video]
        self.end = False
        self.load_file('web/index.html')
        self.expand()
        self.monitor_thread = launch_thread(self._monitor_notifications)

    def _monitor_notifications(self):
        print('Monitoring notifications ...')
        while True:
            if self.end:
                break
            try:
                notification = self.notifier.queue.get_nowait()
                self._notify(notification)
            except queue.Empty:
                time.sleep(1/10)
            except Exception as exc:
                print('Exception while sending notification:')
                traceback.print_tb(exc.__traceback__)
                print(type(exc).__name__)
                print(exc)
                print()
        print('End monitoring.')

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
        self.load_videos()
        self.notifier.notify(DatabaseReady())

    @sciter.script
    def close_app(self):
        self.end = True
        if self.thread:
            self.thread.join()

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
    def get_video_fields(self, index, fields):
        video = self.videos[index]
        values = {}
        for field in fields:
            value = getattr(video, field)
            values[field] = value if isinstance(value, (str, int, float, bool)) else str(value)
        return values

    @sciter.script
    def open_video(self, index):
        self.videos[index].filename.open()

    @sciter.script
    def open_random_video(self, page_size):
        video_index = random.randrange(len(self.videos))
        page_index = video_index // page_size
        shift = video_index % page_size
        self.videos[video_index].filename.open()
        return page_index, shift

    @sciter.script
    def load_videos(self):
        self.videos = sorted(self.api.database.videos(), key=lambda v: v.title)

    @sciter.script
    def search_videos(self, text, cond):
        terms = functions.string_to_pieces(text)
        video_filter = VIDEO_FILTERS[cond]
        self.videos = [video for video in self.api.database.videos() if video_filter(video, terms)]
        self.videos.sort(key=lambda v: v.title)


def main():
    frame = Frame()
    frame.run_app()
    print('End')


if __name__ == '__main__':
    main()
