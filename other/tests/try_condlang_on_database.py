from collections import namedtuple
from typing import Sequence

from pysaurus.application.application import Application
from pysaurus.core import condlang
from pysaurus.database.database import Database


def db_select(
    self: Database, entry: str, fields: Sequence[str], *cond, **kwargs
) -> namedtuple:
    attributes = {field for field in fields if not field.startswith(":")}
    properties = {field for field in fields if field.startswith(":")}
    cls_fields = set(attributes)
    if entry == "video":
        attributes.update(("filename", "video_id"))
        cls_fields.update(("filename", "video_id"))
        source = self.query()
        if properties:
            cls_fields.add("properties")
    elif entry == "property":
        attributes.add("name")
        cls_fields.add("name")
        source = self.prop_types.values()
        assert not properties
    else:
        raise ValueError(f"Unknown database entry: {entry}")
    if cond:
        (condition,) = cond
        assert isinstance(condition, str)
        test = condlang.cond_lang(condition)
        print(test.pretty())

        def selector(el):
            return test(namespace=el)

    else:

        def selector(el):
            return el.match_json(**kwargs)

    cls = namedtuple("DbRow", cls_fields)
    return [
        cls(**el.extract_attributes(attributes | properties))
        for el in source
        if selector(el)
    ]


def main():
    app = Application()
    db = app.open_database_from_name("adult videos")
    cl = db_select(
        db,
        "video",
        [":actress"],
        'readable and "actress" in properties and len(properties["actress"]) > 1',
    )
    print(len(cl))


if __name__ == "__main__":
    main()
