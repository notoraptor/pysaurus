import videre

from pysaurus.interface.using_videre.path_set_view import PathSetView


def main():
    window = videre.Window()
    window.controls = [
        videre.Column(
            [videre.Container(PathSetView(), weight=1), videre.Text("Hello !...")],
            weight=1,
        )
    ]
    window.run()


if __name__ == "__main__":
    main()
