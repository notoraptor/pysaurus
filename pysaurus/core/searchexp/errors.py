class ExpressionError(Exception):
    __slots__ = ("position", "length", "source")

    def __init__(self, message: str, position: int, length: int = 1):
        super().__init__(message)
        self.position = position
        self.length = length
        self.source: str | None = None

    def format_message(self) -> str:
        """Format the error with source context, if available.

        Returns a multi-line string like::

            width > "hello"
                  ^^
            Cannot compare int with str
        """
        msg = str(self)
        if self.source is None:
            return msg
        marker = " " * self.position + "^" * self.length
        return f"{self.source}\n{marker}\n{msg}"
