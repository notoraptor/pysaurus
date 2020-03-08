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

JSON_INTEGER_MIN = -2**31
JSON_INTEGER_MAX = 2**31 - 1


def to_js_value(value):
    if isinstance(value, (str, float, bool, type(None))):
        return value
    if isinstance(value, int) and JSON_INTEGER_MIN <= value <= JSON_INTEGER_MAX:
        return value
    return str(value)


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
        self.groups = None  # type: Optional[List[Tuple[Any, List[Video]]]]
        self.group_field = None
        self.group_reverse = None
        self.group_number = 0

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
                if isinstance(notification, DatabaseReady):
                    break
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
                       ensure_miniatures=False,
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
        if self.videos is not self.all_videos:
            if not self.all_videos:
                self.all_videos = list(self.api.database.videos())
            self.groups = None
            self.group_field = None
            self.group_reverse = None
            self.videos = self.all_videos
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
        return {field: to_js_value(getattr(video, field)) for field in fields}

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
            if self.all_videos:
                self.all_videos = []
            if self.groups is not None and len(self.videos) <= 1:
                self.groups.pop(self.group_number)
                self.group_number = max(0, min(self.group_number, len(self.groups) - 1))
                self.videos = self.groups[self.group_number] if self.groups else []
            return True
        except OSError:
            return False

    @sciter.script
    def rename_video(self, index, new_title):
        video = self.videos[index]
        try:
            self.api.database.change_video_file_title(video, new_title)
            return {'filename': to_js_value(video.filename), 'file_title': video.file_title}
        except OSError as exc:
            return {'error': str(exc)}

    @sciter.script
    def group_videos(self, field, reverse):
        grouped_videos = {}
        for video in self.api.database.videos():
            value = getattr(video, field)
            grouped_videos.setdefault(value, []).append(video)
        filtered_groups = {value: videos for value, videos in grouped_videos.items() if len(videos) > 1}
        groups = [filtered_groups[value] for value in sorted(filtered_groups.keys(), reverse=reverse)]
        self.groups = groups
        self.group_field = field
        self.group_reverse = reverse
        self.group_number = 0
        self.videos = self.groups[self.group_number] if self.groups else []
        self._sort_videos()

    @sciter.script
    def count_groups(self):
        return 0 if self.groups is None else len(self.groups)

    @sciter.script
    def set_group(self, index):
        if index != self.group_number:
            self.videos = self.groups[index]
            self.group_number = index
            self._sort_videos()

    @sciter.script
    def get_group_field_value(self):
        return to_js_value(getattr(self.videos[0], self.group_field))


def main():
    Frame().run_app()
    print('End')


if __name__ == '__main__':
    main()
