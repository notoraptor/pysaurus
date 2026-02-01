"""
High-level database operations that wrap AbstractDatabase methods.

This class provides convenient operations that combine multiple low-level
database calls or add business logic on top of basic CRUD operations.

All methods delegate to AbstractDatabase abstract methods, allowing
subclasses (like PysaurusCollection) to override them with optimized implementations.
"""

from typing import Collection

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.datestring import Date
from pysaurus.database.property_value_modifier import PropertyValueModifier
from pysaurus.properties.properties import PropUnitType, PropValueType


class DatabaseOperations:
    """High-level operations that use AbstractDatabase interface."""

    __slots__ = ("db",)

    def __init__(self, db):
        """
        Initialize DatabaseOperations with a database instance.

        Args:
            db: An AbstractDatabase instance
        """
        from pysaurus.database.abstract_database import AbstractDatabase

        self.db: AbstractDatabase = db

    def set_folders(self, folders) -> None:
        """Set database folders, saving if they changed."""
        folders = sorted(AbsolutePath.ensure(folder) for folder in folders)
        if folders != sorted(self.db.get_folders()):
            self.db._set_folders(folders)
            self.db.save()

    def count_videos(self, *flags, **forced_flags) -> int:
        """Count videos matching given flags."""
        forced_flags.update({flag: True for flag in flags})
        if forced_flags:
            forced_flags.setdefault("discarded", False)
        return self.db.get_videos(
            include=["video_id"], where=forced_flags, count_only=True
        )

    def has_video(self, **fields) -> bool:
        """Check if a video exists matching given fields."""
        return self.db.get_videos(include=(), where=fields, exists_only=True)

    def get_video_filename(self, video_id: int) -> AbsolutePath:
        """Get filename for a video."""
        (row,) = self.db.get_videos(include=["filename"], where={"video_id": video_id})
        return row.filename

    def open_video(self, video_id: int):
        """Open video file and mark as watched."""
        (video,) = self.db.get_videos(
            include=["filename"], where={"video_id": video_id}
        )
        video.filename.open()
        self.mark_as_watched(video_id)

    def mark_as_watched(self, video_id: int):
        """Mark video as watched with current timestamp."""
        self.db.videos_set_field("date_entry_opened", {video_id: Date.now().time})
        self.db.videos_set_field("watched", {video_id: True})

    def mark_as_read(self, video_id: int) -> bool:
        """Toggle watched status and return new value."""
        (row,) = self.db.get_videos(where={"video_id": video_id})
        self.db.videos_set_field("watched", {video_id: not row.watched})
        (row,) = self.db.get_videos(where={"video_id": video_id})
        return row.watched

    def delete_video(self, video_id: int) -> AbsolutePath:
        """Delete video file and database entry."""
        video_filename = self.get_video_filename(video_id)
        video_filename.delete()
        self.db.video_entry_del(video_id)
        return video_filename

    def trash_video(self, video_id: int) -> AbsolutePath:
        """Move video file to system trash and delete database entry."""
        from send2trash import send2trash

        video_filename = self.get_video_filename(video_id)
        send2trash(str(video_filename))
        self.db.video_entry_del(video_id)
        return video_filename

    def change_video_file_title(self, video_id: int, new_title: str) -> None:
        """Change video file title."""
        from pysaurus.application import exceptions
        from pysaurus.core import functions

        if functions.has_discarded_characters(new_title):
            raise exceptions.InvalidFileName(new_title)
        old_filename: AbsolutePath = self.get_video_filename(video_id)
        if old_filename.file_title != new_title:
            self.db.video_entry_set_filename(
                video_id, old_filename.new_title(new_title)
            )

    def move_video_entry(self, from_id: int, to_id: int) -> None:
        """Move a single video entry."""
        from pysaurus.database import database_algorithms

        alg = database_algorithms.DatabaseAlgorithms(self.db)
        alg.move_video_entries([(from_id, to_id)])

    def set_similarities(self, similarities: dict[int, int | None]):
        """Set similarity IDs for videos."""
        self.db.videos_set_field("similarity_id", similarities)
        self._notify_fields_modified(["similarity_id"], is_property=False)

    def set_similarities_from_list(
        self, video_indices: list[int], similarities: list[int | None]
    ):
        """Set similarities from parallel lists."""
        return self.set_similarities(
            {
                video_id: similarity_id
                for video_id, similarity_id in zip(video_indices, similarities)
            }
        )

    def apply_on_prop_value(self, prop_name: str, mod_name: str) -> None:
        """Apply a modifier function to property values."""
        assert "a" <= mod_name[0] <= "z"
        function = getattr(PropertyValueModifier(), mod_name)
        assert self.db.get_prop_types(name=prop_name, with_type=str)
        modified = {}
        for video_id, values in self.db.videos_tag_get(prop_name).items():
            new_values = [function(value) for value in values]
            if values and new_values != values:
                modified[video_id] = new_values
        if modified:
            self.set_property_for_videos(prop_name, modified)

    def count_property_for_videos(
        self, video_indices: list[int], name: str
    ) -> list[list]:
        """Count property values for given videos."""
        from collections import Counter

        count = Counter()
        for values in self.db.videos_tag_get(name, indices=video_indices).values():
            count.update(values)
        return sorted(list(item) for item in count.items())

    def update_property_for_videos(
        self,
        video_indices: list[int],
        name: str,
        values_to_add: list,
        values_to_remove: list,
    ) -> None:
        """Update property by adding/removing values."""
        values_to_add = set(self.validate_prop_values(name, values_to_add))
        values_to_remove = set(self.validate_prop_values(name, values_to_remove))
        old_props = self.db.videos_tag_get(name, indices=video_indices)
        self.set_property_for_videos(
            name,
            {
                video_id: (
                    (set(old_props.get(video_id, ())) - values_to_remove)
                    | values_to_add
                )
                for video_id in video_indices
            },
        )

    def set_property_for_videos(
        self, name: str, updates: dict[int, Collection[PropUnitType]], merge=False
    ):
        """Set property for many videos and notify."""
        self.db.videos_tag_set(
            name,
            updates,
            action=(self.db.action.ADD if merge else self.db.action.REPLACE),
        )
        self._notify_fields_modified([name], is_property=True)

    def validate_prop_values(self, name, values: list) -> list[PropValueType]:
        """Validate property values according to property type."""
        from pysaurus.properties.properties import PropTypeValidator

        (prop_dict,) = self.db.get_prop_types(name=name)
        prop_type = PropTypeValidator(prop_dict)
        if prop_type.multiple:
            values = prop_type.validate(values)
        else:
            values = [prop_type.validate(value) for value in values]
        return values

    def _notify_fields_modified(self, fields, *, is_property=False):
        """Notify that fields were modified."""
        self.db.provider.manage_attributes_modified(
            list(fields), is_property=is_property
        )
        self.db.save()
