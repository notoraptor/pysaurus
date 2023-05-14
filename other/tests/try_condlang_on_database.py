from collections import namedtuple
from typing import Iterable, Sequence, Union

from pysaurus.application.application import Application
from pysaurus.core import condlang
from pysaurus.database.database import Database
from pysaurus.video import Video


def _get_video_fields(
    video: Video, attributes: Iterable[str], properties: Iterable[str] = None
):
    output = {key: getattr(video, key) for key in attributes}
    if properties:
        output["properties"] = {name: video.get_property(name) for name in properties}
    return output


class GetProperty(condlang.Apply):
    __slots__ = ()

    def __init__(self):
        super().__init__(["get_property"], 1)

    def run(self, name: str, namespace: Video, **kwargs):
        database = namespace.database
        values = database.get_prop_values(namespace.video_id, name)
        if database.has_prop_type(name, multiple=True):
            return values
        else:
            (value,) = values or (database.default_prop_unit(name),)
            return value


def db_select_videos(
    self: Database,
    *,
    attributes: Sequence[str] = None,
    properties: Sequence[str] = None,
    where: Union[str, dict] = None
) -> namedtuple:
    if not where:
        return []

    attributes = set(attributes or ()) | {"filename", "video_id"}
    cls_fields = set(attributes)
    if properties:
        cls_fields.add("properties")

    if isinstance(where, str):
        assert isinstance(where, str)
        test = condlang.cond_lang(where, applies=[GetProperty()])
        print(test.pretty())

        def selector(el: Video):
            return test(namespace=el)

    else:
        assert isinstance(where, dict)

        def selector(el: Video):
            return all(getattr(el, key) == value for key, value in where.items())

    cls = namedtuple("DbRow", cls_fields)
    return [
        cls(**_get_video_fields(el, attributes, properties))
        for el in self.get_cached_videos()
        if selector(el)
    ]


def main():
    app = Application()
    db = app.open_database_from_name("adult videos")
    cl = db_select_videos(
        db,
        properties=["actress"],
        where='len(get_property("actress")) > 1',
    )
    print(len(cl))


if __name__ == "__main__":
    main()
