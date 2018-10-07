def __default_manager(notification):
    print(notification)


__MANAGERS = {}
__CALL_DEFAULT_MANAGER = True
__CALL_DEFAULT_MANAGER_BEFORE = True
__DEFAULT_MANAGER = __default_manager


def __set_default_manager_call(integer):
    global __CALL_DEFAULT_MANAGER
    global __CALL_DEFAULT_MANAGER_BEFORE
    if integer == -1:
        __CALL_DEFAULT_MANAGER = True
        __CALL_DEFAULT_MANAGER_BEFORE = True
    if integer == 0:
        __CALL_DEFAULT_MANAGER = False
        __CALL_DEFAULT_MANAGER_BEFORE = True
    if integer == 1:
        __CALL_DEFAULT_MANAGER = True
        __CALL_DEFAULT_MANAGER_BEFORE = False


def get_default_manager():
    return __DEFAULT_MANAGER


def set_default_manager(manager_fn):
    global __DEFAULT_MANAGER
    __DEFAULT_MANAGER = manager_fn


def call_default_manager_before():
    __set_default_manager_call(-1)


def call_default_manager_after():
    __set_default_manager_call(1)


def never_call_default_manager():
    __set_default_manager_call(0)


def register(notification_class, manager_fn):
    __MANAGERS.setdefault(notification_class, []).append(manager_fn)


def unregister(notification_class, manager_fn):
    if notification_class in __MANAGERS:
        __MANAGERS[notification_class].remove(manager_fn)


def unregister_all(notification_class):
    __MANAGERS.pop(notification_class, None)


def notify(notification):
    if __CALL_DEFAULT_MANAGER and __CALL_DEFAULT_MANAGER_BEFORE:
        __DEFAULT_MANAGER(notification)
    notification_class = type(notification)
    if notification_class in __MANAGERS:
        for manager_fn in __MANAGERS[notification_class]:
            manager_fn(notification)
    if __CALL_DEFAULT_MANAGER and not __CALL_DEFAULT_MANAGER_BEFORE:
        __DEFAULT_MANAGER(notification)
