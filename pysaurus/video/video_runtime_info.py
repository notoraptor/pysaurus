from dataclasses import dataclass

LEGACY_MTIME_SLACK = 3600.0  # granted once to rows saved without an offset


@dataclass(slots=True)
class VideoRuntimeInfo:
    size: int = 0
    mtime: float = 0.0
    mtime_utc_offset: int | None = None  # local UTC offset (s) when mtime was read
    driver_id: str | None = None
    is_file: bool = False

    def is_same_file(
        self, mtime: float, mtime_utc_offset: int | None, size: int
    ) -> bool:
        """Whether this disk reading is the file saved as (mtime, offset, size).

        FAT-style volumes store local wall time, converted with the offset in
        effect at read time: an untouched file drifts by exactly the change of
        offset between two reads. NTFS and exFAT-with-offset never drift.
        """
        if self.size != size:
            return False
        delta = self.mtime - mtime
        if delta == 0:
            return True
        if mtime_utc_offset is None:
            return abs(delta) == LEGACY_MTIME_SLACK
        if self.mtime_utc_offset is None:
            return False
        # FAT reports L - offset, so the drift is minus the change of offset.
        return delta == mtime_utc_offset - self.mtime_utc_offset
