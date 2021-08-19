import os
import sys
import tempfile

from cefpython3 import cefpython as cef

from pysaurus.interface.cefgui.cef_api import CefAPI


def set_javascript_bindings(browser):
    interface = CefAPI(browser)
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
