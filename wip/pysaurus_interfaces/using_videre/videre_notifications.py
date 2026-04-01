from pysaurus.core.notifications import Notification


class PageNotification(Notification):
    __slots__ = ()


class RequestedDatabaseUpdate(PageNotification):
    __slots__ = ()


class RequestedHomePage(PageNotification):
    __slots__ = ()


class VideoSelected(Notification):
    __slots__ = ("video_id", "selected")

    def __init__(self, video_id: int, selected: bool):
        self.video_id = video_id
        self.selected = selected
