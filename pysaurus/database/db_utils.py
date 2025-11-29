import logging

from pysaurus.core.functions import camel_case_to_snake_case
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
        from pysaurus.database.database_operations import DatabaseOperations

        ops = DatabaseOperations(database)
        self.entries = ops.count_videos()
        self.discarded = ops.count_videos("discarded")
        self.unreadable_not_found = ops.count_videos("unreadable", "not_found")
        self.unreadable_found = ops.count_videos("unreadable", "found")
        self.readable_not_found = ops.count_videos("readable", "not_found")
        self.readable_found_without_thumbnails = ops.count_videos(
            "readable", "found", "without_thumbnails"
        )
        self.valid = ops.count_videos("readable", "found", "with_thumbnails")

    def __str__(self):
        name = camel_case_to_snake_case(type(self).__name__).replace("_", " ")
        name = name[0].upper() + name[1:]
        return (
            f"{name}: {self.entries} entries, {self.discarded} discarded, "
            f"{self.unreadable_not_found} unreadable not found, "
            f"{self.unreadable_found} unreadable found, "
            f"{self.readable_not_found} readable not found, "
            f"{self.readable_found_without_thumbnails} readble found without thumbnails, "
            f"{self.valid} valid"
        )


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
