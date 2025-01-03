from videre import Button, Column, Text, Window, TextInput, Container


def main():
    window = Window()
    button = Button("open context")

    def fancy(*args):
        print("we pass here")
        window.set_context(
            button, Column([Text("hello 1"), Text("hello 2"), Text("hello 3")])
        )

    button.on_click = fancy
    window.controls = [
        Column(
            [
                button,
                TextInput(),
                Container(background_color="green", weight=0.5),
                TextInput(),
            ]
        )
    ]
    window.run()


if __name__ == "__main__":
    main()
