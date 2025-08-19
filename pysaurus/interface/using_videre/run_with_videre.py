import sys

import videre
from pysaurus.core.informer import Informer
from pysaurus.interface.api.gui_api import GuiAPI
from videre.widgets.widget import Widget


class PysaurusBackend:
    def __init__(self):
        self.api = GuiAPI()

    def get_constants(self):
        return self.api.get_constants()

    def get_database_names(self):
        return self.api.application.get_database_names()


class App:
    def __init__(self):
        self.backend = PysaurusBackend()
        self.window = videre.Window("Pysaurus")

    def _display(self, widget: Widget):
        self.window.controls = [
            videre.ScrollView(
                videre.Container(widget, padding=videre.Padding.all(5)),
                wrap_horizontal=True,
            )
        ]

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
            print(form.values())

        self._display(
            videre.Form(
                videre.Column(
                    [
                        videre.Text("Open database", strong=True),
                        videre.Text("Choose a database:"),
                        videre.Dropdown(database_names),
                        videre.Row(
                            [
                                videre.Checkbox(key="update"),
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
