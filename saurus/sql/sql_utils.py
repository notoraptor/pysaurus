class SQLWhereBuilder:
    __slots__ = ("_where", "_parameters")

    def __init__(self):
        self._where = []
        self._parameters = []

    def __len__(self):
        return len(self._where)

    def append_field(self, name, value):
        self._where.append(f"{name} = ?")
        self._parameters.append(value)

    def get_clause(self) -> str:
        return " AND ".join(self._where)

    def get_parameters(self) -> list:
        return self._parameters
