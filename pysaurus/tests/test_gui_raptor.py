from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.gui_raptor.api import Event, Window
from pysaurus.core.gui_raptor.rendering import RenderImage
from pysaurus.core.utils.functions import package_dir


def main2():
    image_folder = AbsolutePath.join(package_dir(), '..', '..', 'guiraptor', 'test')
    path_image_1 = AbsolutePath.join(image_folder, "tigre.jpg")
    path_image_2 = AbsolutePath.join(image_folder, "Tigerramki.jpg")
    renders = [
        RenderImage(path_image_1.path, 0, 0, -1, 100),
        RenderImage(path_image_1.path, 20, 20),
        RenderImage(path_image_1.path, 200, 200),
        RenderImage(path_image_2.path, 100, 400),
        RenderImage(path_image_2.path, 300, 600),
    ]
    window = Window(1200, 800, "Hello tigers")
    event = Event()
    with window, event:
        while window.is_open():
            while window.next_event(event):
                if event.is_closed():
                    window.close()
            if window.is_open():
                window.draw(renders)


if __name__ == '__main__':
    main2()
