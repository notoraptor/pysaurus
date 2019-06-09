from pysaurus.core.utils.functions import to_printable

OK = 'ok'
ERROR = 'error'
DATA = 'data'


class ToDict:
    __slots__ = []

    def to_dict(self, **extra):
        dct = {field: getattr(self, field) for field in self.__slots__}
        if extra:
            dct.update(extra)
        return dct

    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % (name, to_printable(getattr(self, name))) for name in sorted(self.__slots__)))


class Request(ToDict):
    __slots__ = ('connection_id', 'request_id', 'name', 'parameters')

    def __init__(self, connection_id, request_id, name, parameters):
        self.connection_id = connection_id
        self.request_id = request_id
        self.name = str(name)
        self.parameters = parameters

    @staticmethod
    def from_dict(dct):
        # type: (dict) -> Request
        if len(dct) != len(Request.__slots__):
            raise Exception('Request: unexpected extra fields.')
        for field in Request.__slots__:
            if field not in dct:
                raise Exception('Request: missing field %s' % field)
        return Request(**dct)


class Response(ToDict):
    __slots__ = ('request_id', 'type')

    def __init__(self, request_id, request_type):
        self.request_id = request_id
        self.type = request_type


class OkResponse(Response):

    def __init__(self, request_id):
        super(OkResponse, self).__init__(request_id, OK)


class ErrorResponse(Response):
    __slots__ = ('error_type', 'message')

    def __init__(self, request_id, message):
        super(ErrorResponse, self).__init__(request_id, ERROR)
        self.error_type = type(self).__name__
        self.message = message

    @staticmethod
    def from_exception(request_id, exception):
        # type: (str, Exception) -> ErrorResponse
        response = ErrorResponse(request_id, str(exception))
        response.error_type = type(exception).__name__
        return response


class DataResponse(Response):
    __slots__ = ('data_type', 'data')

    def __init__(self, request_id, data):
        super(DataResponse, self).__init__(request_id, DATA)
        self.data_type = type(self).__name__
        self.data = data


class Notification(ToDict):
    __slots__ = ('connection_id', 'name', 'parameters')

    def __init__(self, name, parameters, connection_id=None):
        self.connection_id = connection_id
        self.name = name
        self.parameters = parameters
