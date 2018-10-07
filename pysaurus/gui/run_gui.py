# Tutorial example. Doesn't depend on any third party GUI framework.
# Tested with CEF Python v57.0+

import base64
import platform
import sys

from cefpython3 import cefpython as cef

from pysaurus.gui.api import Pysaurus


def html_to_data_uri(html, js_callback=None):
    # This function is called in two ways:
    # 1. From Python: in this case value is returned
    # 2. From Javascript: in this case value cannot be returned because
    #    inter-process messaging is asynchronous, so must return value
    #    by calling js_callback.
    html = html.encode("utf-8", "replace")
    b64 = base64.b64encode(html).decode("utf-8", "replace")
    ret = "data:text/html;base64,{data}".format(data=b64)
    if js_callback:
        js_print(js_callback.GetFrame().GetBrowser(),
                 "Python", "html_to_data_uri",
                 "Called from Javascript. Will call Javascript callback now.")
        js_callback.Call(ret)
    else:
        return ret


def js_print(browser, lang, event, msg):
    # Execute Javascript function "js_print"
    browser.ExecuteFunction("js_print", lang, event, msg)


class GlobalHandler(object):
    def OnAfterCreated(self, browser, **_):
        """Called after a new browser is created."""
        # DOM is not yet loaded.
        print('Browser loaded.')


class LoadHandler(object):
    def OnLoadingStateChange(self, browser, is_loading, **_):
        """Called when the loading state has changed."""
        if not is_loading:
            # Loading is complete. DOM is ready.
            print('DOM ready.')


class DisplayHandler(object):
    def OnConsoleMessage(self, browser, message, **_):
        """Called to display a console message."""
        print('[JAVASCRIPT]', message)


def check_versions():
    ver = cef.GetVersion()
    print("[INFO] CEF {ver}".format(ver=ver["cef_version"]))
    print("[INFO] CEF Python {ver}".format(ver=ver["version"]))
    print("[INFO] Chromium {ver}".format(ver=ver["chrome_version"]))
    print("[INFO] Python {ver} {arch}".format(ver=platform.python_version(), arch=platform.architecture()[0]))
    assert cef.__version__ >= "57.0", "CEF Python v57.0+ required to run this"


def set_global_handler():
    # A global handler is a special handler for callbacks that
    # must be set before Browser is created using
    # SetGlobalClientCallback() method.
    global_handler = GlobalHandler()
    cef.SetGlobalClientCallback("OnAfterCreated", global_handler.OnAfterCreated)


def set_client_handlers(browser):
    client_handlers = [LoadHandler(), DisplayHandler()]
    for handler in client_handlers:
        browser.SetClientHandler(handler)


def set_javascript_bindings(browser):
    pysaurus_api_for_js = Pysaurus(browser)
    bindings = cef.JavascriptBindings(bindToFrames=False, bindToPopups=False)
    bindings.SetObject("Pysaurus", pysaurus_api_for_js)
    browser.SetJavascriptBindings(bindings)


def main():
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    settings = {
        'remote_debugging_port': 8080
    }
    cef.Initialize(settings=settings)
    set_global_handler()
    browser = cef.CreateBrowserSync(url="file:///web/index.html", window_title="Pysaurus")
    set_client_handlers(browser)
    set_javascript_bindings(browser)
    cef.MessageLoop()
    cef.Shutdown()


if __name__ == '__main__':
    main()
