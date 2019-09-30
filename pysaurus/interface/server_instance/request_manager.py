import asyncio
from typing import Callable, Optional

import tornado.concurrent

from pysaurus.core.database.api import API
from pysaurus.interface.common.common_functions import launch_thread
from pysaurus.interface.server.protocol import DataResponse, Request, Response
from pysaurus.interface.server.server import Server
from pysaurus.interface.server_instance import core_notifications, error_responses
from pysaurus.interface.server_instance.server_context import ServerContext
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH

ManagerFunction = Callable[[Server, Request], Optional[Response]]


def to_serializable(mixed):
    if isinstance(mixed, (list, tuple, set)):
        return [to_serializable(value) for value in mixed]
    if isinstance(mixed, dict):
        return {to_serializable(key): to_serializable(value) for (key, value) in mixed.items()}
    if hasattr(mixed, 'to_dict'):
        return mixed.to_dict()
    if hasattr(mixed, 'to_json'):
        return mixed.to_json()
    return mixed


def load_database(context):
    # type: (ServerContext) -> None
    context.api = API(TEST_LIST_FILE_PATH, notifier=context.collector)
    context.api.export_api(context.function_parser)
    context.set_is_loaded()
    context.collector.notify(core_notifications.ServerDatabaseLoaded())


def load_clip(future, context, parameters):
    # type: (tornado.concurrent.Future, ServerContext, dict) -> None
    result = context.function_parser.call('clip_filename', parameters)
    future.set_result(result)


class __RequestManager:

    def load(self, server, request):
        # type: (Server, Request) -> Optional[Response]
        context = server.context  # type: ServerContext
        if context.not_loaded():
            context.set_is_loading()
            launch_thread(load_database, context)
        return DataResponse.from_request(request, context.get_loading_status())

    async def clip_filename(self, server, request):
        # type: (Server, Request) -> Response
        context = server.context  # type: ServerContext
        future = tornado.concurrent.Future()
        launch_thread(load_clip, future, context, request.parameters)
        result = await future
        return DataResponse.from_request(request, to_serializable(result))

    async def manage_request(self, server, request):
        # type: (Server, Request) -> Optional[Response]
        print('Received', request)
        context = server.context  # type: ServerContext
        if hasattr(self, request.name) and callable(getattr(self, request.name)):
            manager = getattr(self, request.name)  # type: ManagerFunction
            return await asyncio.coroutine(manager)(server, request)
        if context.is_loaded() and context.function_parser.has_name(request.name):
            result = context.function_parser.call(request.name, request.parameters)
            return DataResponse.from_request(request, to_serializable(result))
        return error_responses.ErrroUnknownRequest(request)


REQUEST_MANAGER = __RequestManager()
