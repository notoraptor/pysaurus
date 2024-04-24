from pysaurus.core.notifications import Notification
from pysaurus.interface.flet_interface.flet_api_wrapper import FletApiWrapper


class ApiForFlet(FletApiWrapper):
    def _notify(self, notification: Notification) -> None:
        pass
