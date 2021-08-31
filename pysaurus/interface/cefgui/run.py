import os
import sys
import tempfile
import threading

from cefpython3 import cefpython as cef

from pysaurus.interface.cefgui.cef_api import CefAPI


def set_javascript_bindings(browser):
    interface = CefAPI(browser)
    bindings = cef.JavascriptBindings()
    bindings.SetObject("python", interface)
    for name, value in interface.get_constants().items():
        bindings.SetProperty(name, value)
    browser.SetJavascriptBindings(bindings)


def thread_excepthook(arg):
    print("Error occurring in thread:", arg.thread.name)
    cef.PostTask(
        cef.TID_UI, cef.ExceptHook, arg.exc_type, arg.exc_value, arg.exc_traceback
    )


def main():
    # Use cef.ExceptHook to shutdown all CEF processes on error.
    sys.excepthook = cef.ExceptHook
    threading.excepthook = thread_excepthook
    entry_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "web/index.html")
    ).replace("\\", "/")
    url = "file:///" + os.path.abspath(entry_path)
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
    print("Exit.")


if __name__ == "__main__":
    main()
