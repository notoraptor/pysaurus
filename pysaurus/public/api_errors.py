from pysaurus.core.error import PysaurusError


class ApiError(PysaurusError):
    pass


class UnsupportedOS(ApiError):
    pass


class UnknownVideoID(ApiError):
    pass


class MissingVideoNewTitle(ApiError):
    pass


class InvalidPageSize(ApiError):
    pass