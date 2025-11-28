from pysaurus.properties.properties import PROP_UNIT_CONVERTER
from saurus.sql.pysaurus_connection import PysaurusConnection
from saurus.sql.sql_utils import SQLWhereBuilder


def prop_type_search(
    db: PysaurusConnection,
    *,
    name=None,
    with_type=None,
    multiple=None,
    with_enum=None,
    default=None,
) -> list[dict]:
    where_clause = SQLWhereBuilder()
    if name is not None:
        where_clause.append_field("name", name)
    if with_type is not None:
        where_clause.append_field("type", with_type.__name__)
    if multiple is not None:
        where_clause.append_field("multiple", int(bool(multiple)))
    clause = "SELECT property_id, name, type, multiple FROM property"
    if where_clause:
        clause += f" WHERE {where_clause.get_clause()}"

    ret = []
    for row in db.query_all(clause, where_clause.get_parameters()):
        tp = PROP_UNIT_CONVERTER[row["type"]]
        with db:
            enumeration = [
                tp(res["enum_value"])
                for res in db.query(
                    "SELECT enum_value FROM property_enumeration "
                    "WHERE property_id = ? ORDER BY rank ASC",
                    [row["property_id"]],
                )
            ]
        if (
            with_enum is None
            or (len(enumeration) > 1 and set(enumeration) == set(with_enum))
        ) and (default is None or enumeration[0] == default):
            ret.append(
                {
                    "property_id": row["property_id"],
                    "name": row["name"],
                    "type": row["type"],
                    "multiple": row["multiple"],
                    "defaultValues": [] if row["multiple"] else [enumeration[0]],
                    "enumeration": enumeration if len(enumeration) > 1 else None,
                }
            )

    return ret
