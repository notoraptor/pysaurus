from typing import Any, List

from pysaurus.core.constants import UNDEFINED
from pysaurus.core.functions import class_get_public_attributes


class FakeVideo:
    """Wrapper to copy public Video fields (especially excluding database attribute)"""

    def __init__(self, video):
        fields = class_get_public_attributes(type(video))
        self.__dict__.update({field: getattr(video, field) for field in fields})

    def __hash__(self):
        return hash(self.filename)

    def __eq__(self, other):
        return self.filename == other.filename

    def __lt__(self, other):
        return self.filename < other.filename

    def has_property(self, name):
        return name in self.properties

    def get_property(self, name, default_unit=UNDEFINED) -> List[Any]:
        return self.properties.get(
            name, [] if default_unit is UNDEFINED else [default_unit]
        )
