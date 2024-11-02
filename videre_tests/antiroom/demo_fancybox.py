from videre import Button, Column, ScrollView, Text, Window


def main():
    window = Window()

    def fancy(*args):
        window.set_fancybox(
            ScrollView(Column([Text(f"Item {i + 1}") for i in range(100)])),
            buttons=[Button("yes"), Button("NO!")],
        )

    window.controls = [Button("Fancy!", on_click=fancy, square=True)]
    fancy()
    window.run()


if __name__ == "__main__":
    main()
