from pysaurus.interface.common.qt_utils import ExceptHookForQt


class PysaurusQtExceptHook(ExceptHookForQt):
    __slots__ = ("api",)

    def __init__(self, qt_app, api):
        super().__init__(qt_app)
        self.api = api

    def cleanup(self):
        self.api.threads_stop_flag = True
