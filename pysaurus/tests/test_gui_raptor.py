from pysaurus.core.gui_raptor.rendering import RenderImage
from pysaurus.core.gui_raptor.api import Window, Event

def main2():
    renders = [
        RenderImage("/home/notoraptor/Images/tigre.jpg", 0, 0),
        RenderImage("/home/notoraptor/Images/tigre.jpg", 20, 20),
        RenderImage("/home/notoraptor/Images/tigre.jpg", 200, 200),
        RenderImage("/home/notoraptor/Images/Tigerramki.jpg", 100, 400),
        RenderImage("/home/notoraptor/Images/Tigerramki.jpg", 300, 600),
    ]
    window = Window(800, 600)
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
