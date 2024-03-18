from typing import Iterable

from saurus.sql.video_parser import FieldQuery


class SQLWhereBuilder:
    __slots__ = ("_where", "_parameters", "_condition")

    def __init__(self, *, use_or=False):
        self._where = []
        self._parameters = []
        self._condition = "OR" if use_or else "AND"

    def __len__(self):
        return len(self._where)

    def append_field(self, name, value):
        self._where.append(f"{name} = ?")
        self._parameters.append(value)

    def append_query(self, query, *values):
        self._where.append(f"({query})")
        self._parameters.extend(values)

    def append_field_query(self, field_query: FieldQuery):
        self.append_query(str(field_query), *field_query.values)

    def append_query_builder(self, builder):
        # type: (SQLWhereBuilder) -> None
        self.append_query(builder.get_clause(), *builder.get_parameters())

    def get_clause(self) -> str:
        return f" {self._condition} ".join(self._where)

    def get_where_clause(self) -> str:
        return f"WHERE {self.get_clause()}" if self else ""

    def get_parameters(self) -> list:
        return self._parameters

    @classmethod
    def build(cls, queries: Iterable[FieldQuery], *, use_or=False):
        builder = cls(use_or=use_or)
        for query in queries:
            builder.append_field_query(query)
        return builder

    @classmethod
    def combine(cls, builders, use_or=False):
        builder = cls(use_or=use_or)
        for child in builders:
            builder.append_query_builder(child)
        return builder
