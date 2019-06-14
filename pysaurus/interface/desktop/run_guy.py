import sys
import traceback

from PySide2 import QtCore, QtWidgets

from pysaurus.core.database import notifications
from pysaurus.core.notification import Notification
from pysaurus.interface.common.app_context import AppContext
from pysaurus.interface.common.common_functions import launch_thread
from pysaurus.public.api import API


class LoadingFinished(Notification):
    pass


def static_database_loading(context):
    # type: (AppContext) -> None
    context.set_is_loading()
    context.api = API(context.collector)
    context.set_is_loaded()
    context.collector.notify(LoadingFinished())


class NotificationWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()
        self.title = QtWidgets.QLabel('')
        self.content = QtWidgets.QLabel('')
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.content.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.content)
        self.setLayout(self.layout)

    def set_notification(self, title, content):
        self.title.setText(title)
        self.content.setText(content)


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.context = AppContext()
        self.thread_collect_notifications = None
        self.thread_load_database = None

        self.button = QtWidgets.QPushButton("load database")
        self.notification_widget = NotificationWidget()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.notification_widget)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

        self.button.clicked.connect(self.load_database)

    def collect_notifications(self):
        print('Monitoring notifications collector.')
        context = self.context  # type: AppContext
        while True:
            try:
                notif = context.collector.queue.get()  # type: Notification
                if notif is None:
                    break
                title = ''
                content = ''
                if isinstance(notif, notifications.DatabaseLoaded):
                    title = 'Database loaded from disk.'
                    content = """
                    <strong>%s</strong> not found,
                    <strong>%s</strong> unreadable,
                    <strong>%s</strong> valid,
                    <strong>%s</strong> with thumbnails.</span>
                    """ % (notif.not_found,
                           notif.unreadable,
                           notif.valid,
                           notif.thumbnails)
                elif isinstance(notif, notifications.CollectingFiles):
                    title = 'Collecting files in'
                    content = notif.folder
                elif isinstance(notif, notifications.CollectedFiles):
                    title = 'Collected %s file(s).' % notif.count
                elif isinstance(notif, notifications.VideosToLoad):
                    title = '%s video(s) to load.' % notif.total
                elif isinstance(notif, notifications.ThumbnailsToLoad):
                    title = '%s thumbnail(s) to load.' % notif.total
                elif isinstance(notif, notifications.UnusedThumbnails):
                    title = 'Removed %s unused thumbnail(s).' % notif.removed
                elif isinstance(notif, notifications.MissingThumbnails):
                    title = '%s missing thumbnail(s).' % len(notif.names)
                elif isinstance(notif, LoadingFinished):
                    title = 'Database loaded!'
                else:
                    print(notif)
                self.notification_widget.set_notification(title, content)
            except Exception as exc:
                print('Exception while sending notification:')
                traceback.print_tb(exc.__traceback__)
                print(type(exc).__name__)
                print(exc)
                print()

    def load_database(self):
        self.thread_collect_notifications = launch_thread(self.collect_notifications)
        if self.context.is_loaded():
            return
        self.thread_load_database = launch_thread(static_database_loading, self.context)

    def closeEvent(self, event):
        print('CLOSE!')
        if self.thread_load_database:
            self.thread_load_database.join()
        if self.thread_collect_notifications:
            self.context.collector.queue.put(None)
            self.thread_collect_notifications.join()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec_())
