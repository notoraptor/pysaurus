from dataclasses import dataclass


@dataclass(slots=True)
class LazyVideoRuntimeInfo:
    size: int = 0
    mtime: float = 0.0
    driver_id: int = None
    is_file: bool = False
