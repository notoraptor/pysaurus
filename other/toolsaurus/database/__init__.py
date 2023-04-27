from pysaurus.database.db_video_attribute import _DbVideoAttribute


class QualityAttribute(_DbVideoAttribute):
    __slots__ = "min", "max"

    QUALITY_FIELDS = (
        ("quality_compression", 6),  # 0, 1 ?
        ("height", 5),  # 0, 16/9 4k => 2160 ?
        ("width", 4),  # 0, 16/9 4k => 3840 ?
        ("raw_seconds", 3),  # 0, 30 minutes ?
        ("frame_rate", 2),  # 0, 60 fps ?
        ("file_size", 1),
        ("audio_bit_rate", 0.5),
    )
    FIELDS = tuple(t[0] for t in QUALITY_FIELDS)
    TOTAL_LEVEL = sum(t[1] for t in QUALITY_FIELDS)

    def __init__(self, database):
        super().__init__(database)
        self.min = []
        self.max = []

    def _update(self):
        videos = list(self.database.get_cached_videos("readable"))
        if not videos:
            self.min.clear()
            self.max.clear()
            return
        self.min = [
            min(getattr(video, field) for video in videos) for field in self.FIELDS
        ]
        self.max = [
            max(getattr(video, field) for video in videos) for field in self.FIELDS
        ]

    def _get(self, video: Video):
        if video.unreadable:
            return 0
        # REFERENCE: For each field:
        # if min_value == max_value:
        #   assert value == min_value, (value, min_value)
        #   quality = 0
        # else:
        #   quality = (value - min_value) / (max_value - min_value)
        #   assert 0 <= quality <= 1, (quality, field, value, min_value, max_value)
        return (
            sum(
                (
                    0
                    if self.min[i] == self.max[i]
                    else (getattr(video, field) - self.min[i])
                    / (self.max[i] - self.min[i])
                )
                * level
                for i, (field, level) in enumerate(self.QUALITY_FIELDS)
            )
            * 100
            / self.TOTAL_LEVEL
        )
