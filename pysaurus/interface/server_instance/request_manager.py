import asyncio
from typing import Optional, Callable

from pysaurus.interface.common.common_functions import launch_thread
from pysaurus.interface.server.protocol import DataResponse
from pysaurus.interface.server.protocol import Request, Response
from pysaurus.interface.server.server import Server
from pysaurus.interface.server_instance import error_responses, core_notifications
from pysaurus.interface.server_instance.server_context import ServerContext
from pysaurus.public.api import API

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
    context.api = API(context.collector)
    context.api.export_api(context.function_parser)
    context.set_is_loaded()
    context.collector.notify(core_notifications.ServerDatabaseLoaded())


class __RequestManager:

    def load(self, server, request):
        # type: (Server, Request) -> Optional[Response]
        context = server.context  # type: ServerContext
        if context.not_loaded():
            context.set_is_loading()
            launch_thread(load_database, context)
        return DataResponse.from_request(request, context.get_loading_status())

    async def manage_request(self, server, request):
        # type: (Server, Request) -> Optional[Response]
        print('Received', request)
        context = server.context  # type: ServerContext
        if context.is_loaded() and context.function_parser.has_name(request.name):
            result = context.function_parser.call(request.name, request.parameters)
            return DataResponse.from_request(request, to_serializable(result))
        if not hasattr(self, request.name) or not callable(getattr(self, request.name)):
            return error_responses.ErrroUnknownRequest(request)
        manager = getattr(self, request.name)  # type: ManagerFunction
        return await asyncio.coroutine(manager)(server, request)


REQUEST_MANAGER = __RequestManager()
