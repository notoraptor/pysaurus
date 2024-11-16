import videre


def main():
    window = videre.Window()
    window.controls = [
        videre.Column(
            [
                videre.Text("hello"),
                videre.Text("world", color="red"),
                videre.Text("how Are you?", size=30, color="#ffeeaa"),
                videre.Text("hello world", color="cyan"),
            ]
        )
    ]
    window.run()


if __name__ == "__main__":
    main()
