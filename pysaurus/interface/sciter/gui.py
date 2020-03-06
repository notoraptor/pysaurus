import functools
import multiprocessing
import queue
import random
import threading
import time
import traceback
from typing import Optional, List, Tuple, Any

import sciter

from pysaurus.core import functions
from pysaurus.core.components import FileSize, Duration
from pysaurus.core.database.api import API
from pysaurus.core.database.notifications import DatabaseReady
from pysaurus.core.database.video import Video
from pysaurus.core.functions import launch_thread
from pysaurus.core.notification import Notifier, Notification
from pysaurus.interface.common.parallel_notifier import ParallelNotifier
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH


def filter_exact(video, terms):
    return ' '.join(terms) in ' '.join(video.terms())


def filter_and(video, terms):
    video_terms = video.terms(as_set=True)
    return all(term in video_terms for term in terms)


def filter_or(video, terms):
    video_terms = video.terms(as_set=True)
    return any(term in video_terms for term in terms)


VIDEO_FILTERS = {'exact': filter_exact, 'and': filter_and, 'or': filter_or}


DEFAULT_SORTING = ['-date']


class Frame(sciter.Window):

    def __init__(self):
        super().__init__(ismain=True, uni_theme=True)
        self.multiprocessing_manager = multiprocessing.Manager()
        self.notifier = ParallelNotifier(self.multiprocessing_manager.Queue())
        self.monitor_thread = None  # type: Optional[threading.Thread]
        self.db_loading_thread = None  # type: Optional[threading.Thread]
        self.threads_stop_flag = False

        self.api = None  # type: Optional[API]
        self.all_videos = []
        self.videos = []  # type: List[Video]
        self.sorting = DEFAULT_SORTING  # type: List[str]
        self.search_text = ''
        self.search_type = ''
        self.groups = []  # type: List[Tuple[Any, List[Video]]]
        self.group_index = 0

        self.load_file('web/index.html')
        self.expand()

    def _monitor_notifications(self):
        print('Monitoring notifications ...')
        while True:
            if self.threads_stop_flag:
                break
            try:
                notification = self.notifier.queue.get_nowait()
                self._notify(notification)
            except queue.Empty:
                time.sleep(1 / 100)
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
                       reset=False)
        self.load_videos()
        self.notifier.notify(DatabaseReady())

    def _sort_videos(self):
        self.videos.sort(key=functools.cmp_to_key(
            lambda v1, v2: Video.compare_to(v1, v2, self.sorting)))

    def _search_videos(self):
        terms = functions.string_to_pieces(self.search_text)
        video_filter = VIDEO_FILTERS[self.search_type]
        self.videos = [video for video in self.api.database.videos()
                       if video_filter(video, terms)]
        self._sort_videos()

    @sciter.script
    def close_app(self):
        self.threads_stop_flag = True
        if self.db_loading_thread:
            self.db_loading_thread.join()

    @sciter.script
    def load_database(self):
        # Launch monitor thread.
        self.monitor_thread = launch_thread(self._monitor_notifications)
        # Then launch database loading thread.
        self.db_loading_thread = launch_thread(self._load_database)

    @sciter.script
    def load_videos(self):
        if not self.all_videos:
            self.all_videos = list(self.api.database.videos())
        self.videos = list(self.all_videos)
        self.search_text = ''
        self.search_type = ''
        self._sort_videos()

    @sciter.script
    def set_sorting(self, sorting):
        sorting = sorting or DEFAULT_SORTING
        if self.sorting != sorting:
            self.sorting = sorting
            self._sort_videos()

    @sciter.script
    def get_sorting(self):
        return self.sorting

    @sciter.script
    def set_search(self, search_text: str, search_type: str):
        search_text = search_text.strip()
        search_type = search_type.strip()
        if (search_text
                and search_type in VIDEO_FILTERS
                and (search_text != self.search_text
                     or search_type != self.search_type)):
            self.search_text = search_text
            self.search_type = search_type
            self._search_videos()

    @sciter.script
    def get_search(self):
        return self.search_text, self.search_type

    @sciter.script
    def count_videos(self):
        return len(self.videos)

    @sciter.script
    def valid_size(self):
        return str(FileSize(sum(video.file_size for video in self.videos)))

    @sciter.script
    def valid_length(self):
        return str(Duration(sum(video.length.total_microseconds
                                for video in self.videos)))

    @sciter.script
    def count_pages(self, page_size):
        assert page_size > 0
        count = len(self.videos)
        return (count // page_size) + bool(count % page_size)

    @sciter.script
    def get_videos_index_range(self, page_size, page_number):
        if not self.videos:
            return 0, 0
        start = page_size * page_number
        end = min(start + page_size, len(self.videos))
        return start, end

    @sciter.script
    def get_video_fields(self, index, fields):
        video = self.videos[index]
        values = {}
        for field in fields:
            value = getattr(video, field)
            values[field] = (value
                             if isinstance(value, (str, int, float, bool))
                             else str(value))
        return values

    @sciter.script
    def open_video(self, index):
        return str(self.videos[index].filename.open())

    @sciter.script
    def open_containing_folder(self, index):
        video = self.videos[index]
        ret = video.filename.open_containing_folder()
        return str(ret) if ret else None

    @sciter.script
    def open_random_video(self, page_size):
        video_index = random.randrange(len(self.videos))
        page_index = video_index // page_size
        shift = video_index % page_size
        filename = self.videos[video_index].filename.open()
        return page_index, shift, str(filename)

    @sciter.script
    def delete_video(self, index):
        video = self.videos[index]
        try:
            self.api.database.delete_video(video)
            self.videos.pop(index)
            self.all_videos.clear()
            return True
        except OSError:
            return False

    @sciter.script
    def group_videos(self, field, reverse):
        grouped_videos = {}
        for video in self.api.database.videos():
            value = getattr(video, field)
            grouped_videos.setdefault(value, []).append(video)
        groups = [(value, videos)
                  for value, videos
                  in grouped_videos.items()
                  if len(videos) > 1]
        groups.sort(key=lambda t: t[0], reverse=reverse)
        self.groups = groups
        self.group_index = 0
        self.videos = self.groups[self.group_index]
        self._sort_videos()


def main():
    Frame().run_app()
    print('End')


if __name__ == '__main__':
    main()
