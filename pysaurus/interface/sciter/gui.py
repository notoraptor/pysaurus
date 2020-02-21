"""
pip install PySciter
"""
import threading
from typing import Optional

import sciter

from pysaurus.core.database.api import API
from pysaurus.core.notification import Notifier, Notification
from pysaurus.interface.common.common_functions import launch_thread
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH


class DatabaseReady(Notification):
    __slots__ = ()


class Frame(sciter.Window):
    def __init__(self):
        super().__init__(ismain=True, uni_theme=True)
        notifier = Notifier()
        notifier.set_default_manager(self.notify)
        self.api = None
        self.notifier = notifier
        self.thread = None  # type: Optional[threading.Thread]

    def _load_database(self):
        self.api = API(TEST_LIST_FILE_PATH,
                       notifier=self.notifier,
                       ensure_miniatures=False,
                       reset=True)
        self.notifier.notify(DatabaseReady())

    def notify(self, notification):
        # type: (Notification) -> None
        print(notification)
        self.call_function('notify', {
            'name': notification.get_name(),
            'notification': notification.to_dict(),
            'message': str(notification)
        })

    @sciter.script
    def load_database(self):
        self.thread = launch_thread(self._load_database)


def main():
    frame = Frame()
    frame.load_file('web/index.html')
    frame.expand()
    frame.run_app()
    print('End')


if __name__ == '__main__':
    main()
