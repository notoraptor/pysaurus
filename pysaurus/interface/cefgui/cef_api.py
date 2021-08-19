import sys
import traceback

from pysaurus.interface.cefgui.gui_api import GuiAPI


class CefAPI(GuiAPI):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser

    def call(self, name, args, resolve, reject):
        try:
            resolve.Call(getattr(self, name)(*args))
        except Exception as exc:
            traceback.print_tb(exc.__traceback__)
            print(f"{type(exc).__name__}:", exc, file=sys.stderr)
            reject.Call({"name": type(exc).__name__, "message": str(exc)})

    def _notify(self, notification):
        self.browser.ExecuteFunction(
            "NOTIFICATION_MANAGER.call",
            {
                "name": notification.get_name(),
                "notification": notification.to_dict(),
                "message": str(notification),
            },
        )
