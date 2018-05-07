from pysaurus.database.notifications import Message
from pysaurus.utils.common import camel_case_to_snake_case


def _print(notification):
    print('[%s]' % camel_case_to_snake_case(notification.__class__.__name__), notification)


class Notifier(object):
    DEFAULT_BEFORE = -1
    DEFAULT_NEVER = 0
    DEFAULT_AFTER = 1
    __slots__ = '__handlers', '__default_handler', '__call_default', '__next_priority'

    def __init__(self):
        self.__handlers = {}
        self.__default_handler = _print
        self.__call_default = 1
        self.__next_priority = 0

    def set_default_handler(self, callback):
        # callback may be None or a callable.
        self.__default_handler = callback

    def get_default_handler(self):
        return self.__default_handler

    def reset_default_handler(self):
        self.__default_handler = _print

    def set_default_handler_call(self, value: int):
        """ Set default handler calling policy.
        :param value: int in (-1, 0, 1).
            If -1, default handler is called on notification before user-defined handlers (if default handler is set).
            If  0, default handler is never called (not even if there are no user-defined handlers).
            If +1, default handler is called on notification after user-defined handlers (if default handler is set).
            Default policy: 1.
        :return: None
        """
        assert value in (self.DEFAULT_BEFORE, self.DEFAULT_NEVER, self.DEFAULT_AFTER)
        self.__call_default = value

    def add_handler(self, notification_class, callback):
        # notification_class must be a sub-class of AbstractNotification.
        # callback must be a callable.
        if notification_class not in self.__handlers:
            self.__handlers[notification_class] = {callback: self.__next_priority}
        else:
            self.__handlers[notification_class][callback] = self.__next_priority
        self.__next_priority += 1

    def remove_handler(self, notification_class, callback):
        # notification_class must be a sub-class of AbstractNotification.
        # callback must be a callable.
        if notification_class in self.__handlers:
            handlers = self.__handlers[notification_class]
            handlers.pop(callback, None)
            if not handlers:
                self.__handlers.pop(notification_class)

    def clear_handlers(self, notification_class):
        # notification_class must be a sub-class of AbstractNotification.
        self.__handlers.pop(notification_class, None)

    def has_handler(self, notification_class, callback=None):
        return notification_class in self.__handlers and (
                callback is None or callback in self.__handlers[notification_class])

    def notify(self, notification):
        # notification_class must be a sub-class of AbstractNotification.
        notification_class = type(notification)
        if notification_class in self.__handlers:
            if self.__default_handler and self.__call_default == -1:
                self.__default_handler(notification)
            for handler, priority in sorted(self.__handlers[notification_class].items(), key=lambda item: item[1]):
                handler(notification)
            if self.__default_handler and self.__call_default == 1:
                self.__default_handler(notification)
        elif self.__default_handler and self.__call_default:
            self.__default_handler(notification)

    def message(self, *args, **kwargs):
        self.notify(Message(*args, **kwargs))
