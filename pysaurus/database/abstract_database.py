import logging
import tempfile
from abc import ABC, abstractmethod
from collections import Counter
from typing import (
    Collection,
    Container,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import ujson as json

from pysaurus.application import exceptions
from pysaurus.core import functions, notifications
from pysaurus.core.components import AbsolutePath, Date, PathType
from pysaurus.core.miniature import Miniature
from pysaurus.core.modules import ImageUtils
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler
from pysaurus.database.algorithms.miniatures import Miniatures
from pysaurus.database.algorithms.videos import Videos
from pysaurus.database.db_utils import DatabaseSaved, DatabaseToSaveContext
from pysaurus.database.db_way_def import DbWays
from pysaurus.database.property_value_modifier import PropertyValueModifier
from pysaurus.properties.properties import (
    PropRawType,
    PropTypeValidator,
    PropUnitType,
    PropValueType,
)
from pysaurus.video import VideoRuntimeInfo
from pysaurus.video_provider.abstract_video_provider import AbstractVideoProvider
from saurus.language import say
from saurus.sql.video_entry import VideoEntry

logger = logging.getLogger(__name__)


class AbstractDatabase(ABC):
    __slots__ = ("ways", "notifier", "in_save_context", "provider")

    def __init__(
        self,
        db_folder: PathType,
        provider: AbstractVideoProvider,
        notifier=DEFAULT_NOTIFIER,
    ):
        db_folder = AbsolutePath.ensure_directory(db_folder)
        self.ways = DbWays(db_folder)
        self.notifier = notifier
        self.in_save_context = False
        self.provider = provider

    @abstractmethod
    def set_date(self, date: Date):
        raise NotImplementedError()

    @abstractmethod
    def get_folders(self) -> Iterable[AbsolutePath]:
        raise NotImplementedError()

    @abstractmethod
    def set_folders(self, folders) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_prop_types(
        self, *, name=None, with_type=None, multiple=None, with_enum=None, default=None
    ):
        raise NotImplementedError()

    @abstractmethod
    def create_prop_type(
        self,
        name: str,
        prop_type: Union[str, type],
        definition: PropRawType,
        multiple: bool,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def remove_prop_type(self, name):
        raise NotImplementedError()

    @abstractmethod
    def rename_prop_type(self, old_name, new_name):
        raise NotImplementedError()

    @abstractmethod
    def convert_prop_multiplicity(self, name: str, multiple: bool) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_videos(
        self,
        *,
        include: Sequence[str] = None,
        with_moves: bool = False,
        where: dict = None,
    ) -> List[dict]:
        raise NotImplementedError()

    @abstractmethod
    def get_all_video_terms(self) -> Dict[int, List[str]]:
        raise NotImplementedError()

    @abstractmethod
    def get_moves(self) -> Iterable[Tuple[int, List[dict]]]:
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
    def delete_video_entry(self, video_id: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def change_video_entry_filename(
        self, video_id: int, path: AbsolutePath
    ) -> AbsolutePath:
        """Map video to new path in database.

        Return the previous path related to video.
        """
        raise NotImplementedError()

    @abstractmethod
    def _write_videos_field(self, indices: Iterable[int], field: str, values: Iterable):
        raise NotImplementedError()

    @abstractmethod
    def write_new_videos(
        self,
        video_entries: List[VideoEntry],
        runtime_info: Dict[AbsolutePath, VideoRuntimeInfo],
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def _insert_new_thumbnails(self, filename_to_thumb_name: Dict[str, str]) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_all_prop_values(
        self, name: str, indices: List[int] = ()
    ) -> Dict[int, List[PropUnitType]]:
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
    def set_video_properties(
        self, video_id: int, properties: dict, merge=False
    ) -> None:
        """Set many properties for a single video."""
        raise NotImplementedError()

    @abstractmethod
    def _set_property_for_videos(
        self, name: str, updates: Dict[int, Collection[PropUnitType]], merge=False
    ):
        """Set one property for many videos."""
        raise NotImplementedError()

    def refresh(self) -> None:
        self.update()
        self.provider.refresh()

    @Profiler.profile_method()
    def update(self) -> None:
        with self.to_save():
            current_date = Date.now()
            all_files = Videos.get_runtime_info_from_paths(self.get_folders())
            self._update_videos_not_found(all_files)
            files_to_update = self._find_video_paths_for_update(all_files)
            needing_thumbs = list(self._get_collectable_missing_thumbnails())
            new: List[VideoEntry] = []
            expected_thumbs: Dict[str, str] = {}
            thumb_errors: Dict[str, List[str]] = {}
            with tempfile.TemporaryDirectory() as tmp_dir:
                results = Videos.hunt(files_to_update, needing_thumbs, tmp_dir)
                # Possible cases for each result:
                # nothing -> error_info XOR error_thumbnail
                # only info, error_thumbnail ?
                # only thumbnail
                # info and thumbnail
                for result in results:
                    if result.info and result.thumbnail:
                        new.append(result.info)
                        expected_thumbs[result.filename] = result.thumbnail
                    elif result.info:
                        info = result.info
                        info.errors = sorted(
                            set(info.errors) | set(result.error_thumbnail)
                        )
                        new.append(info)
                    elif result.thumbnail:
                        expected_thumbs[result.filename] = result.thumbnail
                    else:
                        new.append(
                            VideoEntry(
                                filename=result.filename,
                                errors=sorted(
                                    set(result.error_info) | set(result.error_thumbnail)
                                ),
                                unreadable=True,
                            )
                        )
                    if result.error_thumbnail:
                        thumb_errors[result.filename] = result.error_thumbnail

                self.set_date(current_date)
                if new:
                    self.write_new_videos(new, all_files)
                if expected_thumbs:
                    with Profiler(say("save thumbnails to db"), self.notifier):
                        self._insert_new_thumbnails(expected_thumbs)

                logger.info(f"Thumbnails generated, deleting temp dir {tmp_dir}")
                # Delete thumbnail files (done at context exit)

            if thumb_errors:
                self.notifier.notify(notifications.VideoThumbnailErrors(thumb_errors))

    def _update_videos_not_found(self, existing_paths: Container[AbsolutePath]):
        """Use given container of existing paths to mark not found videos."""
        rows = self.get_videos(include=["video_id", "filename"])
        indices = [row["video_id"] for row in rows]
        founds = [row["filename"] in existing_paths for row in rows]
        self._write_videos_field(indices, "found", founds)

    def _find_video_paths_for_update(
        self, file_paths: Dict[AbsolutePath, VideoRuntimeInfo]
    ) -> List[str]:
        return sorted(
            file_name.standard_path
            for file_name, file_info in file_paths.items()
            if not self.get_videos(
                include=(),
                where={
                    "filename": file_name,
                    "mtime": file_info.mtime,
                    "file_size": file_info.size,
                    "driver_id": file_info.driver_id,
                },
            )
        )

    def _get_collectable_missing_thumbnails(self) -> Dict[str, int]:
        return {
            video["filename"].path: video["video_id"]
            for video in self.get_videos(
                include=["filename", "video_id"],
                where={"readable": True, "found": True, "without_thumbnails": True},
            )
        }

    @Profiler.profile_method()
    def ensure_miniatures(self) -> List[Miniature]:
        miniatures_path = self.ways.db_miniatures_path
        prev_miniatures = Miniatures.read_miniatures_file(miniatures_path)
        valid_miniatures = {
            filename: miniature
            for filename, miniature in prev_miniatures.items()
            if self.has_video(filename=filename)
            and ImageUtils.THUMBNAIL_SIZE == (miniature.width, miniature.height)
        }

        missing_filenames = [
            video["filename"]
            for video in self.get_videos(
                include=["filename"], where={"readable": True, "with_thumbnails": True}
            )
            if video["filename"] not in valid_miniatures
        ]

        added_miniatures = []
        if missing_filenames:
            tasks = [
                (video["filename"], video["thumbnail_blob"])
                for video in self.get_videos(
                    include=("filename", "thumbnail_blob"),
                    where={"filename": missing_filenames},
                )
            ]
            with Profiler(say("Generating miniatures."), self.notifier):
                added_miniatures = Miniatures.get_miniatures(tasks)

        m_dict: Dict[str, Miniature] = {
            m.identifier: m
            for source in (valid_miniatures.values(), added_miniatures)
            for m in source
        }

        if len(valid_miniatures) != len(prev_miniatures) or len(added_miniatures):
            with open(miniatures_path.path, "w") as output_file:
                json.dump([m.to_dict() for m in m_dict.values()], output_file)

        self.notifier.notify(notifications.NbMiniatures(len(m_dict)))

        filename_to_video_id = {
            AbsolutePath.ensure(row["filename"]): row["video_id"]
            for row in self.get_videos(
                include=["video_id", "filename"],
                where={
                    "filename": [
                        AbsolutePath.ensure(m.identifier) for m in m_dict.values()
                    ]
                },
            )
        }
        for m in m_dict.values():
            m.video_id = filename_to_video_id[AbsolutePath.ensure(m.identifier)]
        return list(m_dict.values())

    def count_videos(self, *flags, **forced_flags) -> int:
        forced_flags.update({flag: True for flag in flags})
        return len(self.get_videos(include=["video_id"], where=forced_flags))

    def move_video_entry(self, from_id: int, to_id: int) -> None:
        self._move_video_entries([(from_id, to_id)])

    def confirm_unique_moves(self) -> int:
        unique_moves = self.get_unique_moves()
        self._move_video_entries(unique_moves)
        return len(unique_moves)

    def get_unique_moves(self) -> List[Tuple[int, int]]:
        return [
            (video_id, moves[0]["video_id"])
            for video_id, moves in self.get_moves()
            if len(moves) == 1
        ]

    def _move_video_entries(self, moves: List[Tuple[int, int]]):
        if not moves:
            return
        with self.to_save():
            from_indices = [move[0] for move in moves]
            to_indices = [move[1] for move in moves]
            from_map = {
                row["video_id"]: row
                for row in self.get_videos(
                    include=(
                        "video_id",
                        "similarity_id",
                        "date_entry_modified",
                        "date_entry_opened",
                        "properties",
                    ),
                    where={"video_id": from_indices, "found": False},
                )
            }
            assert all(from_id in from_map for from_id in from_indices)
            assert set(to_indices) == set(
                row["video_id"]
                for row in self.get_videos(
                    include=["video_id"], where={"video_id": to_indices, "found": True}
                )
            )
            to_properties: Dict[str, Dict[int, list]] = {}
            for from_id, to_id in moves:
                from_props: Dict[str, list] = from_map[from_id]["properties"]
                for prop_name, from_prop_values in from_props.items():
                    to_properties.setdefault(prop_name, {})[to_id] = from_prop_values
            # Update properties
            for prop_name, updates in to_properties.items():
                self._set_property_for_videos(prop_name, updates, merge=True)
            # Update attributes
            self._write_videos_field(
                to_indices,
                "similarity_id",
                [from_map[from_id]["similarity_id"] for from_id in from_indices],
            )
            self._write_videos_field(
                to_indices,
                "date_entry_modified",
                [
                    from_map[from_id]["date_entry_modified"].time
                    for from_id in from_indices
                ],
            )
            self._write_videos_field(
                to_indices,
                "date_entry_opened",
                [
                    from_map[from_id]["date_entry_opened"].time
                    for from_id in from_indices
                ],
            )
            for from_id in from_indices:
                self.delete_video_entry(from_id)

    def set_similarities(self, indices: Iterable[int], values: Iterable[Optional[int]]):
        self._write_videos_field(indices, "similarity_id", values)
        self._notify_fields_modified(["similarity_id"])

    def has_video(self, **fields) -> bool:
        return bool(self.get_videos(include=(), where=fields))

    def open_video(self, video_id: int):
        (video,) = self.get_videos(include=["filename"], where={"video_id": video_id})
        AbsolutePath.ensure(video["filename"]).open()
        self._write_videos_field([video_id], "date_entry_opened", [Date.now().time])

    def delete_video(self, video_id: int) -> AbsolutePath:
        video_filename = self.get_video_filename(video_id)
        video_filename.delete()
        self.delete_video_entry(video_id)
        return video_filename

    def change_video_file_title(self, video_id: int, new_title: str) -> None:
        if functions.has_discarded_characters(new_title):
            raise exceptions.InvalidFileName(new_title)
        old_filename: AbsolutePath = self.get_video_filename(video_id)
        if old_filename.file_title != new_title:
            self.change_video_entry_filename(
                video_id, old_filename.new_title(new_title)
            )

    def get_video_filename(self, video_id: int) -> AbsolutePath:
        (row,) = self.get_videos(include=["filename"], where={"video_id": video_id})
        return AbsolutePath.ensure(row["filename"])

    def count_property_for_videos(
        self, video_indices: List[int], name: str
    ) -> List[List]:
        count = Counter()
        for values in self.get_all_prop_values(name, indices=video_indices).values():
            count.update(values)
        return sorted(list(item) for item in count.items())

    def update_property_for_videos(
        self,
        video_indices: List[int],
        name: str,
        values_to_add: list,
        values_to_remove: list,
    ) -> None:
        print(
            "Edit",
            len(video_indices),
            "video props, add",
            values_to_add,
            "remove",
            values_to_remove,
        )
        values_to_add = set(self.validate_prop_values(name, values_to_add))
        values_to_remove = set(self.validate_prop_values(name, values_to_remove))
        old_props = self.get_all_prop_values(name, indices=video_indices)
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

    def move_property_values(
        self, values: list, from_name: str, to_name: str, *, concatenate=False
    ) -> int:
        assert self.get_prop_types(name=from_name, multiple=True)
        assert self.get_prop_types(name=to_name, with_type=str)
        self.validate_prop_values(from_name, values)
        if concatenate:
            (concat_path,) = self.validate_prop_values(
                to_name, [" ".join(str(value) for value in values)]
            )
            to_extended = [concat_path]
        else:
            to_extended = values
        path_set = set(values)
        from_new = {}
        for video_id, old_values in self.get_all_prop_values(from_name).items():
            new_values = [v for v in old_values if v not in path_set]
            if len(old_values) > len(new_values) and (
                not concatenate or len(old_values) == len(new_values) + len(path_set)
            ):
                from_new[video_id] = new_values
        if from_new:
            self._set_property_for_videos(from_name, from_new)
            self._set_property_for_videos(
                to_name, {video_id: to_extended for video_id in from_new}, merge=True
            )
            self._notify_properties_modified([from_name, to_name])
        return len(from_new)

    def delete_property_values(self, name: str, values: list) -> List[int]:
        values = set(self.validate_prop_values(name, values))
        modified = {}
        for video_id, previous_values in self.get_all_prop_values(name).items():
            previous_values = set(previous_values)
            new_values = previous_values - values
            if len(previous_values) > len(new_values):
                modified[video_id] = new_values
        if modified:
            self.set_property_for_videos(name, modified)
        return list(modified.keys())

    def replace_property_values(
        self, name: str, old_values: list, new_value: object
    ) -> bool:
        modified = {}
        old_values = set(self.validate_prop_values(name, old_values))
        (new_value,) = self.validate_prop_values(name, [new_value])
        for video_id, previous_values in self.get_all_prop_values(name).items():
            previous_values = set(previous_values)
            next_values = previous_values - old_values
            if len(previous_values) > len(next_values):
                next_values.add(new_value)
                modified[video_id] = next_values
        if modified:
            self.set_property_for_videos(name, modified)
        return bool(modified)

    def fill_property_with_terms(self, prop_name: str, only_empty=False) -> None:
        assert self.get_prop_types(name=prop_name, with_type=str, multiple=True)
        old = self.get_all_prop_values(prop_name)
        terms = self.get_all_video_terms()
        modified = {
            video_id: video_terms
            for video_id, video_terms in terms.items()
            if not only_empty or not old.get(video_id)
        }
        if modified:
            self.set_property_for_videos(prop_name, modified, merge=True)

    def apply_on_prop_value(self, prop_name: str, mod_name: str) -> None:
        assert "a" <= mod_name[0] <= "z"
        function = getattr(PropertyValueModifier(), mod_name)
        assert self.get_prop_types(name=prop_name, with_type=str)
        modified = {}
        for video_id, values in self.get_all_prop_values(prop_name).items():
            new_values = [function(value) for value in values]
            if values and new_values != values:
                modified[video_id] = new_values
        if modified:
            self.set_property_for_videos(prop_name, modified)

    def set_property_for_videos(
        self, name: str, updates: Dict[int, Collection[PropUnitType]], merge=False
    ):
        """Set property for many videos and notify about property modified."""
        self._set_property_for_videos(name, updates, merge)
        self._notify_properties_modified([name])

    def _notify_properties_modified(self, properties):
        self.provider.manage_attributes_modified(list(properties), is_property=True)
        self.save()

    def _notify_fields_modified(self, fields: Sequence[str]):
        self.provider.manage_attributes_modified(list(fields), is_property=False)
        self.save()

    def validate_prop_values(self, name, values: list) -> List[PropValueType]:
        (prop_dict,) = self.get_prop_types(name=name)
        prop_type = PropTypeValidator(prop_dict)
        if prop_type.multiple:
            values = prop_type.validate(values)
        else:
            values = [prop_type.validate(value) for value in values]
        return values

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
        return self.ways.db_folder.title

    def rename(self, new_name: str) -> None:
        if new_name.startswith("."):
            raise exceptions.PysaurusError(
                f"Database name must not start with dot: {new_name}"
            )
        self.ways = self.ways.renamed(new_name)
