from typing import Optional

from pysaurus.core.classes import ToDict
from pysaurus.core.database.video import Video


class SearchDef(ToDict):
    __slots__ = "text", "cond"
    __none__ = True

    def __init__(self, text: Optional[str], cond: Optional[str]):
        self.text = text.strip() if text else None
        self.cond = cond.strip() if cond else None
        if not self.cond or not hasattr(Video, "has_terms_%s" % self.cond):
            self.cond = "and"

    def __bool__(self):
        return bool(self.text)

    def __eq__(self, other):
        return self.text == other.text and self.cond == other.cond
