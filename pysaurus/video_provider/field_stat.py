from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class FieldStat:
    is_property: bool
    value: Any
    count: int

    def to_dict(self) -> dict:
        return {
            "value": self.value if self.is_property else str(self.value),
            "count": self.count,
        }
