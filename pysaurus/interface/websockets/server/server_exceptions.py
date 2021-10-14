class ServerError(Exception):
    pass


class RequestMissingFieldError(ServerError):
    pass


class RequestUnexpectedExtraFields(ServerError):
    pass


class ServerAlreadyRunningOnPort(ServerError):
    pass
