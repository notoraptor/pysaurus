class ExpressionError(Exception):
    __slots__ = ("position", "length")

    def __init__(self, message: str, position: int, length: int = 1):
        super().__init__(message)
        self.position = position
        self.length = length
