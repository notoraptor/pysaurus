import time

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
        self.window.controls = [videre.ScrollView(widget, wrap_horizontal=True)]

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
        self.window.run_later_async(self._goto_homepage)

    def _goto_homepage(self):
        time.sleep(4)
        database_names = self.backend.get_database_names()
        self._display(
            videre.Column(
                [videre.Text("Choose a database:"), videre.Dropdown(database_names)]
            )
        )

    def start(self):
        with Informer.default():
            try:
                self.welcome()
                self.window.run()
            finally:
                self.backend.api.close_app()


def main():
    App().start()


if __name__ == "__main__":
    main()
