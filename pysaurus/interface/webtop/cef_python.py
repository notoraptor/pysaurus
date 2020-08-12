import os
import sys
import tempfile

from cefpython3 import cefpython as cef


class Interface:
    def __init__(self, browser):
        self.browser = browser
        self.name = 'from python'

    def __call_javascript(self, *args):
        self.browser.ExecuteFunction(*args)

    def print(self, *args):
        print(*args)

    def get_name(self, callback):
        callback.Call(self.name)
        self.__call_javascript('test')


def set_javascript_bindings(browser):
    interface = Interface(browser)
    bindings = cef.JavascriptBindings()
    bindings.SetObject("python", interface)
    browser.SetJavascriptBindings(bindings)


def main():
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    entry_path = os.path.normpath(os.path.join(os.path.dirname(__file__), 'web/index.html')).replace('\\', '/')
    url = 'file:///' + entry_path
    settings = {
        "debug": True,
        "log_severity": cef.LOGSEVERITY_INFO,
        # "log_file": "debug.log",
        "remote_debugging_port": 4000,
        # todo: cache path should be cleared when program is closed ?
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


if __name__ == '__main__':
    main()
