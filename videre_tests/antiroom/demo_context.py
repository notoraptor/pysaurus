import videre
from videre import (
    Alignment,
    Button,
    Column,
    Container,
    Padding,
    Text,
    TextInput,
    TextWrap,
    Window,
)
from videre.layouts.reactive_container import Reactive


def main():
    window = Window()
    window.controls = [
        Column(
            [
                TextInput(),
                Container(background_color="green", weight=0.5),
                TextInput(),
                videre.Row(
                    [
                        videre.Dropdown([1, 2, 3, 4, 100_000]),
                        videre.Container(
                            Reactive(videre.Text("Hello", height_delta=0)),
                            padding=videre.Padding(left=10),
                        ),
                        videre.Container(
                            videre.Button("Hello"), padding=videre.Padding(left=10)
                        ),
                    ]
                ),
                Container(
                    Text(
                        "Hello, World! How are you? "
                        "I'm fine, thanks, and you? I am ok, too, dear!",
                        wrap=TextWrap.WORD,
                    ),
                    background_color="yellow",
                    weight=0.5,
                    horizontal_alignment=Alignment.CENTER,
                    padding=Padding.all(50),
                ),
                Button(
                    "Hello, World! How are you? "
                    "I'm fine, thanks, and you? I am ok, too, dear!",
                    weight=0.5,
                ),
            ]
        )
    ]
    window.run()


if __name__ == "__main__":
    main()
