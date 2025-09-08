import sys
from typing import Any, Callable

import videre
from ovld import OvldMC
from videre.widgets.widget import Widget

from pysaurus.application.exceptions import PysaurusError
from pysaurus.core.constants import VIDEO_DEFAULT_PAGE_NUMBER, VIDEO_DEFAULT_PAGE_SIZE
from pysaurus.core.informer import Information
from pysaurus.core.notifications import DatabaseReady, End, Notification
from pysaurus.interface.using_videre.backend import PysaurusBackend
from pysaurus.interface.using_videre.process_page import ProcessPage
from pysaurus.interface.using_videre.videos_page import VideosPage
from pysaurus.interface.using_videre.videre_notifications import RequestedDatabaseUpdate


class App(metaclass=OvldMC):
    def __init__(self):
        self.container = videre.Container(padding=videre.Padding.all(5))
        self.window = videre.Window("Pysaurus", alert_on_exceptions=[PysaurusError])
        self.window.controls = [self.container]
        self.backend = PysaurusBackend(self.window)

    def start(self) -> int:
        with Information():
            try:
                self.welcome_page()
                return self.window.run()
            finally:
                self.backend.close_app()

    def _display(self, widget: Widget, callback=None):
        # Clear notification callback before displaying new page
        self.window.clear_notification_callbacks()
        self.window.add_notification_callback(self.on_notification)
        if callback:
            self.window.add_notification_callback(callback)
        # Set new page to display
        self.container.control = widget

    def on_notification(self, notification: Notification):
        pass

    def on_notification(self, notification: RequestedDatabaseUpdate):
        self.database_update_page()

    def welcome_page(self):
        self._display(
            videre.Column([videre.Text("Welcome to Pysaurus!"), videre.Progressing()])
        )
        self.window.call_async(self.home_page)

    def home_page(self):
        database_names = self.backend.get_database_names()

        self._display(
            videre.Form(
                videre.Column(
                    [
                        videre.Text("Open database", strong=True),
                        videre.Text("Choose a database:"),
                        videre.Dropdown(database_names, name="name"),
                        videre.Row(
                            [
                                videre.Checkbox(key="update", name="update"),
                                videre.Label(
                                    for_button="update", text="Update on load"
                                ),
                            ],
                            vertical_alignment=videre.Alignment.CENTER,
                        ),
                        videre.SubmitButton("Open", on_submit=self._open_database_page),
                    ],
                    space=5,
                ),
                key="form",
            )
        )

    def _open_database_page(self, fields: dict[str, Any]):
        self.database_page(name=fields["name"], update=fields["update"])

    def database_page(self, name: str, update: bool):
        self.process_page(
            title="Open database",
            procedure=videre.Procedure(self.backend.open_database, name, update),
            on_end=self.videos_page,
        )

    def database_update_page(self):
        self.process_page(
            title="Update database",
            procedure=videre.Procedure(self.backend.update_database),
            on_end=self.videos_page,
        )

    def process_page(
        self,
        *,
        title: str,
        procedure: videre.Procedure | Callable[[], Any],
        on_end: Callable[[End], None],
    ):
        process_page = ProcessPage(title, callback=on_end)
        self._display(process_page, callback=process_page.on_notification)
        self.window.call_later(procedure)

    def videos_page(self, end_notification: End):
        assert isinstance(end_notification, DatabaseReady)
        context = self.backend.get_python_backend(
            VIDEO_DEFAULT_PAGE_SIZE, VIDEO_DEFAULT_PAGE_NUMBER
        )
        videos_page = VideosPage(context)
        self._display(videos_page, callback=videos_page.on_notification)


def main():
    sys.exit(App().start())


if __name__ == "__main__":
    main()
