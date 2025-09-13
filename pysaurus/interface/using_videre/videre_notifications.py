from pysaurus.core.notifications import Notification


class PageNotification(Notification):
    __slots__ = ()


class RequestedDatabaseUpdate(PageNotification):
    __slots__ = ()


class RequestedHomePage(PageNotification):
    __slots__ = ()
