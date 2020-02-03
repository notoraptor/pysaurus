"""
pip install PySciter
"""
import sciter
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH
from pysaurus.core.database.api import API
from pysaurus.core.notification import Notifier, Notification
from pysaurus.interface.common.common_functions import launch_thread
import threading


class DatabaseReady(Notification):
    __slots__ = ()


class SciterNotifier(Notifier):
    def __init__(self, frame):
        # type: (Frame) -> None
        super().__init__()
        self.set_default_manager(frame.notify)


class Frame(sciter.Window):
    def __init__(self):
        super().__init__(ismain=True, uni_theme=True)
        self.api = None
        self.notifier = SciterNotifier(self)
        self.thread = None  # type: threading.Thread

    def _load_database(self):
        self.api = API(TEST_LIST_FILE_PATH, notifier=self.notifier, ensure_miniatures=False)
        self.notifier.notify(DatabaseReady())

    @sciter.script
    def load_database(self):
        self.thread = launch_thread(self._load_database)

    def notify(self, notification):
        # type: (Notification) -> None
        print(notification)
        self.call_function('notify', {
            'name': notification.get_name(),
            'notification': notification.to_dict(),
            'message': str(notification)
        })


def main():
    frame = Frame()
    frame.load_file('web/index.html')
    frame.expand()
    frame.run_app()
    print('End')

if __name__ == '__main__':
    main()
