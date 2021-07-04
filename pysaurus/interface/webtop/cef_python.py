import os
import sys
import tempfile
import traceback

import pyperclip
from cefpython3 import cefpython as cef

from pysaurus.interface.webtop.gui_api import GuiAPI


class Interface(GuiAPI):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser

    def clipboard(self, text):
        pyperclip.copy(text)

    def call(self, name, args, resolve, reject):
        try:
            resolve.Call(getattr(self, name)(*args))
        except Exception as exc:
            traceback.print_tb(exc.__traceback__)
            print(f"{type(exc).__name__}:", exc, file=sys.stderr)
            reject.Call({"name": type(exc).__name__, "message": str(exc)})

    def _notify(self, notification):
        print(notification)
        self.browser.ExecuteFunction(
            "NOTIFICATION_MANAGER.call",
            {
                "name": notification.get_name(),
                "notification": notification.to_dict(),
                "message": str(notification),
            },
        )


def set_javascript_bindings(browser):
    interface = Interface(browser)
    bindings = cef.JavascriptBindings()
    bindings.SetObject("python", interface)
    for name, value in interface.get_constants().items():
        bindings.SetProperty(name, value)
    browser.SetJavascriptBindings(bindings)


def main():
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    entry_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "web/index.html")
    ).replace("\\", "/")
    url = "file:///" + entry_path
    settings = {
        "debug": False,
        "log_severity": cef.LOGSEVERITY_INFO,
        # "log_file": "debug.log",
        "remote_debugging_port": 4000,
        "cache_path": tempfile.gettempdir(),
    }
    switches = {
        # prevent local CORS exceptions.
        "disable-web-security": ""
    }
    cef.Initialize(settings=settings, switches=switches)
    browser = cef.CreateBrowserSync(url=url, window_title="Pysaurus")
    set_javascript_bindings(browser)
    cef.MessageLoop()
    cef.Shutdown()


if __name__ == "__main__":
    main()
