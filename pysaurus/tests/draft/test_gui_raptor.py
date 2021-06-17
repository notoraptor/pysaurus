from pysaurus.core.components import AbsolutePath
from pysaurus.core.functions import package_dir
from pysaurus.core.native.gui_raptor import rendering
from pysaurus.core.native.gui_raptor.api import Event, TextInfo, Window


def main():
    image_folder = AbsolutePath.join(package_dir(), '..', '..', 'cysaurus', 'other', 'test', 'gui', 'resource')
    path_image_1 = AbsolutePath.join(image_folder, "tigre.jpg")
    path_image_2 = AbsolutePath.join(image_folder, "Tigerramki.jpg")
    text = rendering.PatternText(content="Hello World! 漢字漢字 漢字! See you soon!", size=50)
    with TextInfo(text) as text_info:
        print(text_info.length)
        print(text_info.width)
        print(text_info.height)
        print(text_info.top)
        print(text_info.left)
        print(text_info.coordinates)
    frame = rendering.PatternFrame(x=100, y=100, width=400, height=500, patterns=[
        rendering.PatternImage(src=path_image_1.path, height=100, y=80),
        rendering.PatternImage(src=path_image_1.path, x=20, y=60),
        rendering.PatternImage(src=path_image_1.path, x=200, y=200),
        rendering.PatternImage(src=path_image_2.path, x=100, y=400),
        rendering.PatternImage(src=path_image_2.path, x=300, y=420),
        text
    ])
    window = Window(1200, 800, "Hello tigers")
    event = Event()
    with window, event:
        while window.is_open():
            while window.next_event(event):
                if event.is_closed():
                    window.close()
            if window.is_open():
                # window.draw(elements)
                window.draw([frame])


if __name__ == '__main__':
    main()
