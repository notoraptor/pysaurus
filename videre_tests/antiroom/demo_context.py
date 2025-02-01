import videre
from videre import Column, Container, TextInput, Window


def main():
    window = Window()
    window.controls = [
        Column(
            [
                TextInput(),
                Container(background_color="green", weight=0.5),
                TextInput(),
                videre.Dropdown([1, 2, 3, 4, 100_000]),
                Container(background_color="yellow", weight=0.5),
            ]
        )
    ]
    window.run()


if __name__ == "__main__":
    main()
