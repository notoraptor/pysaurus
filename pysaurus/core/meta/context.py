class Context:
    __slots__ = ['_context']

    def __init__(self):
        self._context = False

    def __getattribute__(self, item):
        if not object.__getattribute__(self, '_context'):
            raise RuntimeError('%s object not used as a context' % type(self).__name__)
        return object.__getattribute__(self, item)

    def on_exit(self):
        pass

    def __enter__(self):
        self._context = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.on_exit()
        self._context = False
