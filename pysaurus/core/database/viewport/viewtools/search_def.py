from typing import Optional

from pysaurus.core.classes import ToFulLDict


class SearchDef(ToFulLDict):
    __slots__ = "text", "cond"

    def __init__(self, text: Optional[str], cond: Optional[str]):
        self.text = text.strip() if text else None
        self.cond = cond.strip() if cond else "and"

    def __bool__(self):
        return bool(self.text)
