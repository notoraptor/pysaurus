import enum
import logging
from abc import ABC, abstractmethod
from typing import Any, Collection, Iterable, Literal, Sequence, overload

from pysaurus.application import exceptions
from pysaurus.core.absolute_path import AbsolutePath, PathType
from pysaurus.core.datestring import Date
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.database.database_algorithms import DatabaseAlgorithms
from pysaurus.database.database_operations import DatabaseOperations
from pysaurus.database.db_utils import DatabaseSaved, DatabaseToSaveContext
from pysaurus.database.db_way_def import DbWays
from pysaurus.properties.properties import PropRawType, PropUnitType
from pysaurus.video import VideoRuntimeInfo
from pysaurus.video.video_entry import VideoEntry
from pysaurus.video.video_pattern import VideoPattern
from pysaurus.video_provider.abstract_video_provider import AbstractVideoProvider

logger = logging.getLogger(__name__)


class Change(enum.StrEnum):
    ADD = enum.auto()
    REMOVE = enum.auto()
    REPLACE = enum.auto()


class AbstractDatabase(ABC):
    """
    Abstract base class for database implementations.

    ARCHITECTURE NOTES (2024):
    ---------------------------
    This class has been refactored to provide a minimal interface:

    - **AbstractDatabase**: Contains ONLY abstract methods (interface) and essential utilities
    - **DatabaseOperations** (database_operations.py): High-level operations (count, get, set, validate)
    - **DatabaseAlgorithms** (database_algorithms.py): Complex algorithms (update, miniatures, moves)

    All high-level operations have been moved to DatabaseOperations and DatabaseAlgorithms.
    Code should now use these classes instead of calling methods directly on AbstractDatabase.
    AbstractDatabase provides two properties to easily use these classes:
    - ops: returns a DatabaseOperations
    - algos: returns a DatabaseAlgorithms

    Benefits:
    - Minimal interface: only ~20 abstract methods to implement
    - Clear separation: interface vs operations vs algorithms
    - Better maintainability: logic is separated from persistence layer
    - Subclass optimizations still work via delegation
    """

    __slots__ = ("ways", "notifier", "in_save_context", "provider")
    action = Change

    def __init__(
        self,
        db_folder: PathType,
        provider: AbstractVideoProvider,
        notifier=DEFAULT_NOTIFIER,
    ):
        db_folder = AbsolutePath.ensure(db_folder).assert_dir()
        self.ways = DbWays(db_folder)
        self.notifier = notifier
        self.in_save_context = False
        self.provider = provider

    @abstractmethod
    def _set_date(self, date: Date):
        raise NotImplementedError()

    @abstractmethod
    def get_folders(self) -> Iterable[AbsolutePath]:
        raise NotImplementedError()

    @abstractmethod
    def _set_folders(self, folders: list[AbsolutePath]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_prop_types(
        self, *, name=None, with_type=None, multiple=None, with_enum=None, default=None
    ) -> list[dict]:
        raise NotImplementedError()

    @abstractmethod
    def prop_type_add(
        self, name: str, prop_type: str | type, definition: PropRawType, multiple: bool
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def prop_type_del(self, name):
        raise NotImplementedError()

    @abstractmethod
    def prop_type_set_name(self, old_name, new_name):
        raise NotImplementedError()

    @abstractmethod
    def prop_type_set_multiple(self, name: str, multiple: bool) -> None:
        raise NotImplementedError()

    @overload
    def get_videos(
        self,
        *,
        include: Sequence[str] = None,
        with_moves: bool = False,
        where: dict = None,
        # Optimization flags
        count_only: Literal[True],
        exists_only: Literal[False] = False,
    ) -> int: ...

    @overload
    def get_videos(
        self,
        *,
        include: Sequence[str] = None,
        with_moves: bool = False,
        where: dict = None,
        # Optimization flags
        count_only: Literal[False] = False,
        exists_only: Literal[True],
    ) -> bool: ...

    @overload
    def get_videos(
        self,
        *,
        include: Sequence[str] = None,
        with_moves: bool = False,
        where: dict = None,
        # Optimization flags
        count_only: Literal[False] = False,
        exists_only: Literal[False] = False,
    ) -> list[VideoPattern]: ...

    @abstractmethod
    def get_videos(
        self,
        *,
        include: Sequence[str] = None,
        with_moves: bool = False,
        where: dict = None,
        # Optimization flags
        count_only: bool = False,
        exists_only: bool = False,
    ) -> list[VideoPattern] | int | bool:
        raise NotImplementedError()

    @abstractmethod
    def videos_get_terms(self) -> dict[int, list[str]]:
        raise NotImplementedError()

    @abstractmethod
    def videos_get_moves(self) -> Iterable[tuple[int, list[dict]]]:
        """
        Return an iterable of potential moves.
        Each potential move is represented by a couple:
        - The video ID of the (not found) vido which may have been moved.
        - A list of dictionaries, each describing
          a potential destination (found) video. Required fields:
          - "video_id" : video ID of destination video.
          - "filename": standard path of destination video.
        """
        raise NotImplementedError()

    @abstractmethod
    def video_entry_del(self, video_id: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def video_entry_set_filename(
        self, video_id: int, path: AbsolutePath
    ) -> AbsolutePath:
        """Map video to new path in database.

        Return the previous path related to video.
        """
        raise NotImplementedError()

    @abstractmethod
    def videos_set_field(self, field: str, changes: dict[int, Any]):
        raise NotImplementedError()

    @abstractmethod
    def videos_add(
        self,
        video_entries: list[VideoEntry],
        runtime_info: dict[AbsolutePath, VideoRuntimeInfo],
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def _thumbnails_add(self, filename_to_thumb_name: dict[str, str]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def videos_tag_get(
        self, name: str, indices: list[int] = ()
    ) -> dict[int, list[PropUnitType]]:
        """
        Return all values for given property
        :param name: name of property
        :param indices: indices of video to get property values.
            Default is all videos.
        :return: a dictionary mapping a video ID to the list
            of property values associated to this video for this
            property in the database.
        """
        raise NotImplementedError()

    @abstractmethod
    def video_entry_set_tags(
        self, video_id: int, properties: dict, merge=False
    ) -> None:
        """Set many properties for a single video."""
        raise NotImplementedError()

    @abstractmethod
    def videos_tag_set(
        self,
        name: str,
        updates: dict[int | None, Collection[PropUnitType]],
        action: Change = Change.REPLACE,
    ):
        """
        Set one property for many videos.

        :param name: property name
        :param updates: dict mapping a video ID to property values
            If there is only 1 key which is None in the dict,
            then all video indices will be updated.
        :param action: update policy (for each video ID):
            - "replace" (default): replace old values with new values
            - "add": add new values to existing values
            - "remove": remove given values from existing values
        """
        raise NotImplementedError()

    def _notify_fields_modified(self, fields: Sequence[str], *, is_property=False):
        """Notify provider that fields were modified and save database."""
        self.provider.manage_attributes_modified(list(fields), is_property=is_property)
        self.save()

    def to_save(self):
        """Return a save context.

        Save context forbids any save while in context,
        and make a save as long as we exit the context.

        This is useful if a piece of code may generate many save calls
        while we just want one final save at the end.
        """
        return DatabaseToSaveContext(self)

    def save(self):
        """Save database.

        Do not save if we're in a save context returned by `to_save`.
        Otherwise, save using private method _save().
        """
        # Do not save if in save context
        if self.in_save_context:
            logger.info("Saving deactivated in context.")
            return
        # We can save. Save database.
        self._save()
        # Notify database is saved.
        self.notifier.notify(DatabaseSaved(self))

    def _save(self):
        """Actually saves database.

        Do nothing by default, as database may have automatic save.
        If your database must be manually saved, consider overriding this method.
        """
        pass

    def __close__(self):
        """Close database."""
        logger.info(f"Database closed: {self.get_name()}")

    def reopen(self):
        pass

    def get_name(self) -> str:
        """Get database name."""
        return self.ways.db_folder.title

    def rename(self, new_name: str) -> None:
        if new_name.startswith("."):
            raise exceptions.PysaurusError(
                f"Database name must not start with dot: {new_name}"
            )
        self.ways = self.ways.renamed(new_name)

    @property
    def ops(self) -> DatabaseOperations:
        return DatabaseOperations(self)

    @property
    def algos(self) -> DatabaseAlgorithms:
        return DatabaseAlgorithms(self)
