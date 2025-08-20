import sys

import videre
from pysaurus.core.informer import Informer
from pysaurus.core.notifications import Notification
from pysaurus.interface.api.gui_api import GuiAPI
from pysaurus.interface.using_videre.process_page import ProcessPage
from videre.widgets.widget import Widget


class _VidereGuiAPI(GuiAPI):
    __slots__ = ("window",)

    def __init__(self) -> None:
        super().__init__()
        self.window: videre.Window | None = None

    def _notify(self, notification: Notification) -> None:
        if self.window:
            self.window.notify(notification)


class PysaurusBackend:
    def __init__(self):
        self.api = _VidereGuiAPI()

    def get_constants(self):
        return self.api.get_constants()

    def get_database_names(self):
        return self.api.application.get_database_names()


class App:
    def __init__(self):
        self.backend = PysaurusBackend()
        self.window = videre.Window("Pysaurus")
        self.backend.api.window = self.window

    def _display(self, widget: Widget):
        # Clear notification callback before displaying new page
        self.window.set_notification_callback(None)
        # Set new page to display
        self.window.controls = [videre.Container(widget, padding=videre.Padding.all(5))]

    def display_test_page(self):
        constants = self.backend.get_constants()
        self._display(
            videre.Column(
                [
                    videre.Row(
                        [
                            videre.Text(f"{key}: ", weight=1),
                            videre.Text(
                                repr(value), wrap=videre.TextWrap.WORD, weight=1
                            ),
                        ]
                    )
                    for key, value in constants.items()
                ],
                expand_horizontal=True,
            )
        )

    def welcome(self):
        self._display(
            videre.Column([videre.Text("Welcome to Pysaurus!"), videre.Progressing()])
        )
        self.window.run_async(self._goto_homepage)

    def _goto_homepage(self):
        database_names = self.backend.get_database_names()

        def _get_form(*args):
            form: videre.Form = self.window.get_element_by_key("form")
            fields = form.values()
            self._goto_database_page(name=fields["name"], update=fields["update"])

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

    def _goto_database_page(self, name: str, update: bool):
        process_page = ProcessPage("Opening database ...")
        self._display(process_page)
        self.window.set_notification_callback(process_page.on_notification)
        self.window.run_async(self.backend.api.open_database, name, update)

    def start(self) -> int:
        with Informer.default():
            try:
                self.welcome()
                return self.window.run()
            finally:
                self.backend.api.close_app()


def main():
    sys.exit(App().start())


if __name__ == "__main__":
    main()
