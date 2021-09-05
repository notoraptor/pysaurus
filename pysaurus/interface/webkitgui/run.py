import os
import sys
import traceback

import ujson as json
import webview

from pysaurus.application import exceptions
from pysaurus.core.components import AbsolutePath
from pysaurus.core.functions import package_dir
from pysaurus.interface.cefgui.gui_api import GuiAPI


class PyWebViewAPI(GuiAPI):
    def __init__(self, window):
        super().__init__()
        self.window = window

    def _notify(self, notification):
        jsnstr = json.dumps(
            {
                "name": type(notification).__name__,
                "notification": notification.to_dict(),
                "message": str(notification),
            }
        )
        self.window.evaluate_js(f"window.NOTIFICATION_MANAGER.call({jsnstr})")

    def call(self, name, args):
        try:
            return getattr(self, name)(*args)
        except exceptions.PysaurusError as exc:
            traceback.print_tb(exc.__traceback__)
            print(f"{type(exc).__name__}:", exc, file=sys.stderr)
            raise exc

    def on_load(self):
        print("Load frontend constants.")
        js_commands = []
        for name, value in self.get_constants().items():
            js_commands.append(f"window.{name} = {json.dumps(value)};")
        js_commands.append("document.documentElement.style.zoom = 1.75;")
        self.window.evaluate_js("\n".join(js_commands))


def main():
    entry_path = AbsolutePath.join(
        package_dir(), "interface", "cefgui", "web", "index.html"
    )
    relative_path = os.path.relpath(entry_path.path)
    api = PyWebViewAPI(None)
    window = webview.create_window(
        title="Pysaurus", url=relative_path, js_api=api, width=2000, height=1000
    )
    api.window = window
    webview.start(gui="qt", debug=True, func=api.on_load)


if __name__ == "__main__":
    main()
