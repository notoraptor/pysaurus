class VideoRaptorResult:
    __slots__ = ('done', 'errors')

    def __init__(self, *, done=None, errors=None):
        self.done = done
        self.errors = errors

    def __str__(self):
        if self.done:
            return str(self.done)
        return str(self.errors)
