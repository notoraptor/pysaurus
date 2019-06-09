class ApiError(Exception):
    pass


class UnsupportedOS(ApiError):
    pass


class UnknownVideoID(ApiError):
    pass


class MissingVideoNewTitle(ApiError):
    pass


class InvalidPageSize(ApiError):
    pass
