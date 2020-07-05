import multiprocessing
import queue
import random
import threading
import time
import traceback
from typing import Optional

import sciter

from pysaurus.core.database.api import API
from pysaurus.core.database.notifications import DatabaseReady
from pysaurus.core.database.video_provider import VideoProvider
from pysaurus.core.functions import launch_thread
from pysaurus.core.notification import Notification
from pysaurus.interface.common.parallel_notifier import ParallelNotifier
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH

JSON_INTEGER_MIN = -2 ** 31
JSON_INTEGER_MAX = 2 ** 31 - 1


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
        self.provider = None  # type: Optional[VideoProvider]

        self.load_file('web/index.html')
        self.expand()

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
        if self.provider:
            self.provider.load()
        else:
            self.provider = VideoProvider(self.api.database)

    @sciter.script
    def set_sorting(self, sorting):
        self.provider.set_sort(sorting)

    @sciter.script
    def get_sorting(self):
        return self.provider.get_sorting()

    @sciter.script
    def set_search(self, search_text: str, search_type: str):
        self.provider.set_search(search_text, search_type)

    @sciter.script
    def count_videos(self):
        return self.provider.count()

    @sciter.script
    def valid_size(self):
        return str(self.provider.get_view_file_size())

    @sciter.script
    def valid_length(self):
        return str(self.provider.get_view_duration())

    @sciter.script
    def count_pages(self, page_size):
        assert page_size > 0
        count = self.count_videos()
        return (count // page_size) + bool(count % page_size)

    @sciter.script
    def get_videos_index_range(self, page_size, page_number):
        nb_videos = self.count_videos()
        if not nb_videos:
            return 0, 0
        start = page_size * page_number
        end = min(start + page_size, nb_videos)
        return start, end

    @sciter.script
    def get_video_fields(self, index, fields):
        video = self.provider.get_video(index)
        return {field: to_js_value(getattr(video, field)) for field in fields}

    @sciter.script
    def open_video(self, index):
        return str(self.provider.get_video(index).filename.open())

    @sciter.script
    def open_containing_folder(self, index):
        video = self.provider.get_video(index)
        ret = video.filename.open_containing_folder()
        return str(ret) if ret else None

    @sciter.script
    def open_random_video(self, page_size):
        nb_videos = self.count_videos()
        video_index = random.randrange(nb_videos)
        page_index = video_index // page_size
        shift = video_index % page_size
        filename = self.provider.get_video(video_index).filename.open()
        return page_index, shift, str(filename)

    @sciter.script
    def open_not_found(self):
        try:
            return self.api.not_found_html()
        except Exception:
            return False

    @sciter.script
    def delete_video(self, index):
        return self.provider.delete_video(index)

    @sciter.script
    def rename_video(self, index, new_title):
        video = self.provider.get_video(index)
        try:
            self.api.database.change_video_file_title(video, new_title)
            self.provider.check_group()
            return {'filename': to_js_value(video.filename), 'file_title': video.file_title}
        except OSError as exc:
            return {'error': str(exc)}

    @sciter.script
    def group_videos(self, field, reverse):
        self.provider.set_groups(field, reverse)

    @sciter.script
    def count_groups(self):
        return self.provider.count_groups()

    @sciter.script
    def set_group(self, index):
        self.provider.set_group(index)

    @sciter.script
    def get_group_field_value(self):
        return to_js_value(self.provider.get_group_field_value())

    @sciter.script
    def get_info(self, page_size):
        return {
            'nbVideos': self.count_videos(),
            'nbPages': self.count_pages(page_size),
            'validSize': self.valid_size(),
            'validLength': self.valid_length(),
            'nbGroups': self.count_groups(),
        }

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


def main():
    Frame().run_app()
    print('End')


if __name__ == '__main__':
    main()
