from typing import Optional

from pysaurus.core.classes import ToFulLDict, Enumeration

_Cond = Enumeration(("and", "or", "exact"))


class SearchDef(ToFulLDict):
    __slots__ = "text", "cond"

    def __init__(self, text: Optional[str], cond: Optional[str]):
        self.text = text.strip() if text else None
        self.cond = _Cond(cond.strip() if cond else "and")

    def __bool__(self):
        return bool(self.text)
