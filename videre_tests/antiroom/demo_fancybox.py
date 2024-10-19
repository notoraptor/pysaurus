from videre import Button, Column, Text, Window


def main():
    window = Window()

    def fancy(*args):
        window.set_fancybox(
            Column([Text(f"Item {i + 1}") for i in range(100)]),
            # buttons=[Button("yes"), Button("NO!")],
        )

    window.controls = [Button("Fancy!", on_click=fancy)]
    fancy()
    window.run()


if __name__ == "__main__":
    main()
