from typing import Any

from pysaurus.core.classes import ToDict
from pysaurus.interface.websockets.server.server_exceptions import (
    RequestMissingFieldError,
    RequestUnexpectedExtraFields,
)

OK = "ok"
ERROR = "error"
DATA = "data"
RESPONSE = "response"
NOTIFICATION = "notification"


class Request(ToDict):
    __slots__ = ("connection_id", "request_id", "name", "parameters")

    def __init__(self, connection_id, request_id, name, parameters):
        self.connection_id = connection_id
        self.request_id = request_id
        self.name = str(name)
        self.parameters = parameters

    @staticmethod
    def from_dict(dct):
        # type: (dict) -> Request
        if len(dct) != len(Request.__slots__):
            raise RequestUnexpectedExtraFields()
        for field in Request.__slots__:
            if field not in dct:
                raise RequestMissingFieldError(field)
        return Request(**dct)


class ServerMessage(ToDict):
    __slots__ = ("message_type",)

    def __init__(self, message_type):
        self.message_type = message_type


class Notification(ServerMessage):
    __slots__ = ("connection_id", "name", "parameters")

    def __init__(self, name, parameters, connection_id=None):
        super().__init__(NOTIFICATION)
        self.connection_id = connection_id
        self.name = name
        self.parameters = parameters


class Response(ServerMessage):
    __slots__ = ("request_id", "type")

    def __init__(self, request_id, request_type):
        super().__init__(RESPONSE)
        self.request_id = request_id
        self.type = request_type


class OkResponse(Response):
    __slots__ = ()

    def __init__(self, request_id):
        super().__init__(request_id, OK)


class ErrorResponse(Response):
    __slots__ = ("error_type", "message")

    def __init__(self, request_id, error_type, message):
        super().__init__(request_id, ERROR)
        self.error_type = error_type
        self.message = message

    @staticmethod
    def from_exception(request_id, exception):
        # type: (str, Exception) -> ErrorResponse
        return ErrorResponse(request_id, type(exception).__name__, str(exception))


class DataResponse(Response):
    __slots__ = ("data_type", "data")

    def __init__(self, request_id, data_type, data):
        super().__init__(request_id, DATA)
        self.data_type = data_type
        self.data = data

    @staticmethod
    def from_request(request, data):
        # type: (Request, Any) -> DataResponse
        return DataResponse(request.request_id, request.name, data)


class AutoErrorResponse(ErrorResponse):
    __slots__ = ()

    def __init__(self, request_id, message):
        super().__init__(request_id, type(self).__name__, message)


class AutoDataResponse(DataResponse):
    __slots__ = ()

    def __init__(self, request_id, data):
        super().__init__(request_id, type(self).__name__, data)
