import logging

import videre


def main():
    logging.basicConfig(level=logging.INFO)
    window = videre.Window(background=videre.Colors.gray)
    window.controls = [
        videre.Column(
            [videre.TextInput(weight=1), videre.Text("nothing here!", weight=1)]
        )
    ]
    window.run()


if __name__ == "__main__":
    main()
