import sys

import videre
from videre.widgets.widget import Widget

from pysaurus.core.constants import VIDEO_DEFAULT_PAGE_NUMBER, VIDEO_DEFAULT_PAGE_SIZE
from pysaurus.core.informer import Informer
from pysaurus.core.notifications import DatabaseReady, End
from pysaurus.interface.using_videre.backend import PysaurusBackend
from pysaurus.interface.using_videre.process_page import ProcessPage
from pysaurus.interface.using_videre.videos_page import VideosPage


class App:
    def __init__(self):
        self.container = videre.Container(padding=videre.Padding.all(5))
        self.window = videre.Window("Pysaurus")
        self.window.controls = [self.container]
        self.backend = PysaurusBackend(self.window)

    def start(self) -> int:
        with Informer.default():
            try:
                self.welcome_page()
                return self.window.run()
            finally:
                self.backend.close_app()

    def _display(self, widget: Widget):
        # Clear notification callback before displaying new page
        self.window.set_notification_callback(None)
        # Set new page to display
        self.container.control = widget

    def welcome_page(self):
        self._display(
            videre.Column([videre.Text("Welcome to Pysaurus!"), videre.Progressing()])
        )
        self.window.run_async(self.home_page)

    def home_page(self):
        database_names = self.backend.get_database_names()

        def _get_form(*args):
            form: videre.Form = self.window.get_element_by_key("form")
            fields = form.values()
            self.database_page(name=fields["name"], update=fields["update"])

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
                        videre.Button("Open", on_click=_get_form),
                    ],
                    space=5,
                ),
                key="form",
            )
        )

    def database_page(self, name: str, update: bool):
        process_page = ProcessPage("Open database", callback=self.videos_page)
        self._display(process_page)
        self.window.set_notification_callback(process_page.on_notification)
        self.window.run_later(self.backend.open_database, name, update)

    def videos_page(self, end_notification: End):
        assert isinstance(end_notification, DatabaseReady)
        context = self.backend.get_python_backend(
            VIDEO_DEFAULT_PAGE_SIZE, VIDEO_DEFAULT_PAGE_NUMBER
        )
        videos_page = VideosPage(context, updater=self.backend.get_python_backend)
        self._display(videos_page)
        self.window.set_notification_callback(videos_page.on_notification)


def main():
    sys.exit(App().start())


if __name__ == "__main__":
    main()
