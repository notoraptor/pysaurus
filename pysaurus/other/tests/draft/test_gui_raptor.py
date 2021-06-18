import os

from pysaurus.core.components import AbsolutePath
from pysaurus.other.native.gui_raptor import rendering
from pysaurus.other.native.gui_raptor.api import Event, Window
from pysaurus.other.native.gui_raptor.text_info import TextInfo


def main_old():
    image_folder = AbsolutePath(os.path.dirname(__file__))
    path_image_1 = AbsolutePath.join(image_folder, "tigre.jpg")
    path_image_2 = AbsolutePath.join(image_folder, "Tigerramki.jpg")

    text = rendering.PatternText(content="Hello World! 漢字漢字 漢字! See you soon!", size=50)
    frame = rendering.PatternFrame(
        x=300,
        y=100,
        width=400,
        height=500,
        patterns=[
            rendering.PatternImage(src=path_image_1.path, height=100, y=80),
            rendering.PatternImage(src=path_image_1.path, x=20, y=60),
            rendering.PatternImage(src=path_image_1.path, x=200, y=200),
            rendering.PatternImage(src=path_image_2.path, x=100, y=400),
            rendering.PatternImage(src=path_image_2.path, x=300, y=420),
            text,
        ],
    )

    with TextInfo(text) as text_info:
        print(text_info.length)
        print(text_info.width)
        print(text_info.height)
        print(text_info.left)
        print(text_info.top)
        print(text_info.coordinates)

    window = Window.new(1200, 800, "Hello tigers")
    event = Event.new()
    while Window.is_open(window):
        while Window.next_event(window, event):
            if Event.is_closed(event):
                Window.close(window)
        if Window.is_open(window):
            Window.draw(window, [frame])
    Event.destroy(event)
    Window.destroy(window)
    print("End./.")


def main():
    text = rendering.PatternText(content="Hello World! 漢字漢字 漢字! See you soon!", size=50)
    window = Window.new(1200, 800, "Hello tigers")
    event = Event.new()
    while Window.is_open(window):
        while Window.next_event(window, event):
            if Event.is_closed(event):
                Window.close(window)
        if Window.is_open(window):
            Window.draw(window, [text])
    Event.destroy(event)
    Window.destroy(window)
    print("End./.")


if __name__ == "__main__":
    main()
