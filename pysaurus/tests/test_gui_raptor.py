from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.gui_raptor.api import Event, Window, TextInfo
from pysaurus.core.gui_raptor import patterns
from pysaurus.core.utils.functions import package_dir


def main2():
    image_folder = AbsolutePath.join(package_dir(), '..', '..', 'guiraptor', 'test')
    path_image_1 = AbsolutePath.join(image_folder, "tigre.jpg")
    path_image_2 = AbsolutePath.join(image_folder, "Tigerramki.jpg")
    text = patterns.PatternText(content="Hello World! 漢字漢字 漢字! See you soon!", size=50, font=r"/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc")
    with TextInfo(text) as text_info:
        print(text_info.length)
        print(text_info.width)
        print(text_info.height)
        print(text_info.top)
        print(text_info.left)
        print(text_info.coordinates)
    elements = [
        patterns.PatternImage(src=path_image_1.path, height=100, y=80),
        patterns.PatternImage(src=path_image_1.path, x=20, y=60),
        patterns.PatternImage(src=path_image_1.path, x=200, y=200),
        patterns.PatternImage(src=path_image_2.path, x=100, y=400),
        patterns.PatternImage(src=path_image_2.path, x=300, y=600),
        text
    ]
    frame = patterns.PatternFrame(x=100, y=100, width=400, height=200, patterns=elements)
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
    main2()
