import sys
import traceback

from pysaurus.application import exceptions
from pysaurus.interface.api.gui_api import GuiAPI


class CefAPI(GuiAPI):
    __slots__ = ("browser",)

    def __init__(self, browser):
        super().__init__()
        self.browser = browser

    def call(self, name, args, resolve, reject):
        try:
            resolve.Call(self.__run_feature__(name, *args))
        except exceptions.PysaurusError as exc:
            traceback.print_tb(exc.__traceback__)
            print(f"{type(exc).__name__}:", exc, file=sys.stderr)
            reject.Call({"name": type(exc).__name__, "message": str(exc)})

    def _notify(self, notification):
        self.browser.ExecuteFunction(
            "NOTIFICATION_MANAGER.call",
            {
                "name": type(notification).__name__,
                "notification": notification.to_dict(),
                "message": str(notification),
            },
        )
