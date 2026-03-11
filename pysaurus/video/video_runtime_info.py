from dataclasses import dataclass


@dataclass(slots=True)
class VideoRuntimeInfo:
    size: int = 0
    mtime: float = 0.0
    driver_id: int | None = None
    is_file: bool = False
