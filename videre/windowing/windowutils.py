def on_event(event_type: int):
    """
    Generate a decorator to mark a function as an event manager for given event type.
    Used on Window's event handling methods.

    :param event_type: Pygame event type.
    :return: a decorator
    """

    def decorator(function):
        function.event_type = event_type
        return function

    return decorator
