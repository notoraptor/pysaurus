from pysaurus.core.notifications import Notification
from pysaurus.interface.api.gui_api import GuiAPI


class ApiForFlet(GuiAPI):
    def _notify(self, notification: Notification) -> None:
        pass
