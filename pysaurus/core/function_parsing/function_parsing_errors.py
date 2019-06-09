class FunctionParsingError(Exception):
    pass


class UnknownQuery(FunctionParsingError):
    pass


class InvalidQueryArgCount(FunctionParsingError):
    pass


class MissingQueryArg(FunctionParsingError):
    pass
