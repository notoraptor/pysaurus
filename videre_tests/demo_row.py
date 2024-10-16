import videre


def main():
    window = videre.Window.LD()
    window.controls = [
        videre.Row(
            [
                videre.Rectangle(50, 100, videre.Colors.red),
                videre.Rectangle(60, 50, videre.Colors.green),
                videre.Rectangle(70, 80, videre.Colors.blue),
            ],
            vertical_alignment=videre.Alignment.END,
        )
    ]
    window.run()


if __name__ == "__main__":
    main()
