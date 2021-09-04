from pysaurus.core.function_parsing.function_parser import FunctionParser
from pysaurus.interface.common.app_context import AppContext


class ServerContext(AppContext):
    __slots__ = ('function_parser',)

    def __init__(self):
        super(ServerContext, self).__init__()
        self.function_parser = FunctionParser()
