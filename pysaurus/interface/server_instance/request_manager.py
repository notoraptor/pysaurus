import asyncio
import threading
from typing import Optional, Callable

from pysaurus.interface.server.protocol import Request, Response
from pysaurus.interface.server.server import Server
from pysaurus.interface.server_instance import error_responses, data_responses, core_notifications
from pysaurus.interface.server_instance.server_context import ServerContext
from pysaurus.public.api import API

ManagerFunction = Callable[[Server, Request], Optional[Response]]


def load_database(context):
    # type: (ServerContext) -> None
    context.interface = API(context.collector)
    context.set_is_loaded()
    context.collector.notify(core_notifications.ServerDatabaseLoaded())


def launch_thread(function, *args, **kwargs):
    thread = threading.Thread(target=function, args=args, kwargs=kwargs)
    thread.start()
    return thread


class __RequestManager:

    def load(self, server, request):
        # type: (Server, Request) -> Optional[Response]
        context = server.context  # type: ServerContext
        if context.not_loaded():
            context.set_is_loading()
            launch_thread(load_database, context)
            return None
        if context.is_loading():
            return data_responses.DatabaseIsLoading(request.request_id)
        if context.is_loaded():
            return data_responses.DatabaseAlreadyLoaded(request.request_id)

    async def manage_request(self, server, request):
        # type: (Server, Request) -> Optional[Response]
        print('Received', request)
        if not hasattr(self, request.name) or not callable(getattr(self, request.name)):
            return error_responses.ErrroUnknownRequest(request)
        manager = getattr(self, request.name)  # type: ManagerFunction
        return await asyncio.coroutine(manager)(server, request)


REQUEST_MANAGER = __RequestManager()
