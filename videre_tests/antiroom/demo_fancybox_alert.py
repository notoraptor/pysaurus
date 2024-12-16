from videre import Button, Window


def main():
    window = Window()

    def fancy(*args):
        window.alert("You have an alert")

    window.controls = [Button("Fancy!", on_click=fancy)]
    fancy()
    window.run()


if __name__ == "__main__":
    main()
