from typing import Optional

from pysaurus.core.classes import ToDict
from pysaurus.core.enumeration import Enumeration

_Cond = Enumeration(("and", "or", "exact"))


class SearchDef(ToDict):
    __slots__ = "text", "cond"
    __print_none__ = True

    def __init__(self, text: Optional[str], cond: Optional[str]):
        self.text = text.strip() if text else None
        self.cond = _Cond(cond.strip() if cond else "and")

    def __bool__(self):
        return bool(self.text)
