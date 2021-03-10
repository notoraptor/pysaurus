import webview
from pysaurus.scripts import sebgui
from types import MethodType
from pysaurus.core.modules import ImageUtils
from pysaurus.core.components import AbsolutePath
from io import BytesIO
import base64


def pywebview_load_image(thumb_path):
    thumb_path = AbsolutePath.ensure(thumb_path)
    if not thumb_path.isfile():
        return None
    image = ImageUtils.open_rgb_image(thumb_path.path)
    buffered = BytesIO()
    # image.save(buffered, format=THUMBNAIL_EXTENSION)
    image.save(buffered)
    image_string = base64.b64encode(buffered.getvalue())
    return image_string


class _WebGUI:
    def __init__(self, title, interface):
        self.title = title
        self.interface = interface
        self.window = None

    def _wrap_callable(self, window, fn):
        def wrapper(*args, **kwargs):
            window.load_html(fn(*args, **kwargs))

        wrapper.__name__ = fn.__name__
        return wrapper

    def run(self):
        self.window = webview.create_window(self.title, html=self.interface.index())

        self.window.expose(pywebview_load_image)
        for name in dir(self.interface):
            if name.startswith("_"):
                continue
            method = getattr(self.interface, name)
            if not isinstance(method, MethodType):
                continue
            self.window.expose(self._wrap_callable(self.window, method))

        webview.start(gui="gtk", debug=True)


def web_gui(title, interface):
    return _WebGUI(title, interface).run()


class Interface:
    def __init__(self):
        self._gen = sebgui.HTML()

    def index(self):
        return self._gen(
            'My index code! <button onclick="pywebview.api.test()">click</button>'
        )

    def test(self):
        return self._gen("clicked !")


if __name__ == "__main__":
    _WebGUI("Hello Title !", Interface()).run()
