from copy import deepcopy
from typing import Iterable, List, Optional, Tuple, Union

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


class TableDef:
    __slots__ = ("name", "alias")

    def __init__(self, name: str, alias: str):
        self.name = name
        self.alias = alias

    def get_alias_field(self, name) -> str:
        return f"{self.alias}.{name}"

    def __str__(self):
        return f"{self.name} AS {self.alias}"

    __repr__ = __str__


class JoinDef:
    __slots__ = ("join_table", "main_table", "main_field", "join_field", "left_join")

    def __init__(
        self,
        join_table: TableDef,
        main_table: TableDef,
        join_field: str,
        main_field: str = None,
        left_join=False,
    ):
        self.join_table = join_table
        self.main_table = main_table
        self.join_field = join_field
        self.main_field = main_field or join_field
        self.left_join = left_join

    def __str__(self):
        return (
            f"{'LEFT ' if self.left_join else ''}"
            f"JOIN {self.join_table} "
            f"ON {self.main_table.alias}.{self.main_field} "
            f"= {self.join_table.alias}.{self.join_field}"
        )

    __repr__ = __str__


class OrderField:
    __slots__ = ("table", "field", "reverse")

    def __init__(self, table: TableDef, field: str, reverse=False):
        self.table = table
        self.field = field
        self.reverse = reverse

    def __str__(self):
        return f"{self.table.alias}.{self.field} {'DESC' if self.reverse else 'ASC'}"

    __repr__ = __str__


class QueryMaker:
    __slots__ = (
        "_fields",
        "_main_table",
        "_jointures",
        "where",
        "_order",
        "limit",
        "offset",
    )

    def __init__(self, table_name: str, table_alias: str):
        self._fields: List[str] = []
        self._main_table: Optional[TableDef] = None
        self._jointures: List[JoinDef] = []
        self.where = SQLWhereBuilder()
        self._order: List[Union[OrderField, str]] = []
        self.limit = None
        self.offset = None

        self.set_main_table(table_name, table_alias)

    def __str__(self):
        return self.generate()

    def to_sql(self) -> Tuple[str, list]:
        return str(self), self.where.get_parameters()

    def add_field(self, field: str):
        self._fields.append(field)

    def add_fields(self, fields: Iterable[str]):
        self._fields.extend(fields)

    def set_field(self, field: str):
        self._fields.clear()
        self.add_field(field)

    def set_fields(self, fields: Iterable[str]):
        self._fields.clear()
        self.add_fields(fields)

    def set_main_table(self, name: str, alias: str):
        self._main_table = TableDef(name, alias)

    def get_main_table(self):
        return self._main_table

    def find_table(self, name) -> TableDef:
        if self._main_table and self._main_table.name == name:
            return self._main_table
        for jointure in self._jointures:
            if jointure.join_table.name == name:
                return jointure.join_table
        raise ValueError(f"Query maker: no table found: {name}")

    def add_join(
        self,
        join_table: TableDef,
        join_field: str,
        main_field: str = None,
        left_join=False,
    ):
        join_def = JoinDef(
            join_table, self._main_table, join_field, main_field, left_join=left_join
        )
        self._jointures.append(join_def)

    def add_left_join(self, join_table: TableDef, join_field, main_field=None):
        self.add_join(join_table, join_field, main_field, left_join=True)

    def order_by(self, table: TableDef, field: str, reverse=False):
        self._order.append(OrderField(table, field, reverse))

    def order_by_complex(self, order: str):
        self._order.append(order)

    def copy(self):
        return deepcopy(self)

    def generate(self) -> str:
        """
        SELECT <fields>
        FROM <main_table> AS <main_alias>
        JOIN <join_table> AS <join_alias> ON
             <main_alias>.<main_field> = <join_alias>.<join_field>
        JOIN ...
        WHERE
            [where_pack] = <AND|OR> (where_clause|where_pack ...)
            [where_clause] =|
                <field = value>
                <field in query>
        ORDER BY
            <order_field> <ASC|DESC>
            ...
        LIMIT <starting_row_0_indexed> <n_rows_to_return_from_offset>
        """
        assert self._fields
        assert self._main_table
        query = f"SELECT {','.join(self._fields)} FROM {self._main_table}"
        for jointure in self._jointures:
            query += f" {jointure}"
        if self.where:
            query += " " + self.where.get_where_clause()
        if self._order:
            query += f" ORDER BY {','.join(str(field) for field in self._order)}"
        if self.limit is not None:
            query += f" LIMIT {self.limit}"
        if self.offset is not None:
            query += f" OFFSET {self.offset}"
        return query
