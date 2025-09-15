import inspect

import videre

from pysaurus.interface.using_videre.common import (
    FIELD_MAP,
    FieldInfo,
    FieldType,
    GroupPerm,
    Uniconst,
)
from pysaurus.interface.using_videre.path_set_view import PathSetView
from pysaurus.video.video_pattern import VideoPattern


def get_prop_info(
    prop: property, title: str | None = None, permission: GroupPerm = GroupPerm.ALL
) -> FieldInfo:
    name = prop.__name__
    sig = inspect.signature(prop.fget)
    ret_type = sig.return_annotation
    if ret_type in (bool, int, float, str):
        field_type = getattr(FieldType, ret_type.__name__.upper())
    else:
        if ret_type.__lt__ is object.__lt__:
            field_type = FieldType.UNSORTABLE
        else:
            field_type = FieldType.SORTABLE
    return FieldInfo(name, title, permission, field_type)


def main_uniconst():
    for name in dir(Uniconst):
        if not name.startswith("_"):
            print(name, getattr(Uniconst, name))


def main_try_get_prop_info():
    for field in FIELD_MAP.fields.values():
        guessed = get_prop_info(getattr(VideoPattern, field.name))
        if guessed != field:
            print("DIFF", field.name)
            print(f"\tFIELD\t{field}")
            print(f"\tGUESS\t{guessed}")


def main_try_videre():
    window = videre.Window()
    window.controls = [
        videre.Column(
            [videre.Container(PathSetView(), weight=1), videre.Text("Hello !...")],
            weight=1,
        )
    ]
    window.run()


if __name__ == "__main__":
    main_try_get_prop_info()
