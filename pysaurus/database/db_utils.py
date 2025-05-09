import logging

from pysaurus.core.notifications import Notification

logger = logging.getLogger(__name__)


class DatabaseLoaded(Notification):
    __slots__ = (
        "entries",
        "discarded",
        "unreadable_not_found",
        "unreadable_found",
        "readable_not_found",
        "readable_found_without_thumbnails",
        "valid",
    )
    __slot_sorter__ = list

    def __init__(self, database):
        super().__init__()
        self.entries = database.count_videos()
        self.discarded = database.count_videos("discarded")
        self.unreadable_not_found = database.count_videos("unreadable", "not_found")
        self.unreadable_found = database.count_videos("unreadable", "found")
        self.readable_not_found = database.count_videos("readable", "not_found")
        self.readable_found_without_thumbnails = database.count_videos(
            "readable", "found", "without_thumbnails"
        )
        self.valid = database.count_videos("readable", "found", "with_thumbnails")


class DatabaseSaved(DatabaseLoaded):
    __slots__ = ()


class DatabaseToSaveContext:
    __slots__ = ("database",)

    def __init__(self, database):
        from pysaurus.database.abstract_database import AbstractDatabase

        self.database: AbstractDatabase = database

    def __enter__(self):
        self.database.in_save_context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.database.in_save_context = False
        self.database.save()
        logger.info("Saved in context.")
