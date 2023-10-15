import logging
import tempfile
from multiprocessing import Pool
from typing import (
    Any,
    Callable,
    Container,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Union,
)

from pysaurus.core import notifications
from pysaurus.core.components import AbsolutePath, Date
from pysaurus.core.constants import PYTHON_ERROR_THUMBNAIL
from pysaurus.core.job_notifications import notify_job_start
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database.database import Database as OldDatabase
from pysaurus.database.db_way_def import DbWays
from pysaurus.database.thubmnail_database.thumbnail_manager import ThumbnailManager
from pysaurus.miniature.miniature import Miniature
from pysaurus.properties.properties import DefType, PropValueType
from pysaurus.updates.video_inliner import (
    flatten_video,
    get_flatten_fields,
    get_video_text,
)
from pysaurus.video import Video, VideoRuntimeInfo
from pysaurus.video.video_sorting import VideoSorting
from saurus.language import say
from saurus.sql.pysaurus_collection import PysaurusCollection

logger = logging.getLogger(__name__)


class OldPysaurusCollection(OldDatabase):
    __slots__ = ("db",)

    def __init__(self, path, folders=None, notifier=DEFAULT_NOTIFIER):
        # super().__init__(path, folders, notifier)
        path = AbsolutePath.ensure_directory(path)
        self.notifier = notifier
        self.ways = DbWays(path)
        self.db = PysaurusCollection(self.ways.db_folder.path)
        self.__thumb_mgr = ThumbnailManager(self.ways.db_thumb_sql_path)
        self.notifier.set_log_path(self.ways.db_log_path.path)
        self.__load(folders)

    def __load(self, folders=None):
        if folders:
            new_folders = [AbsolutePath.ensure(path) for path in folders]
            old_folders = set(self.get_folders())
            folders_to_add = [
                (path.path,) for path in new_folders if path not in old_folders
            ]
            if folders_to_add:
                self.db.modify(
                    "INSERT INTO collection_source (source) VALUES (?)",
                    folders_to_add,
                    many=True,
                )
                logger.info(f"Added {len(folders_to_add)} new source(s).")
                # Update discarded videos.
                # Newly added folders can only un-discard previously discarded videos.
                source_tree = PathTree(list(old_folders) + list(new_folders))
                rows = self.db.query_all(
                    "SELECT video_id, filename FROM video WHERE discarded = 1"
                )
                allowed = [
                    row
                    for row in rows
                    if source_tree.in_folders(AbsolutePath(row["filename"]))
                ]
                if allowed:
                    self.db.modify(
                        "UPDATE video SET discarded = 0 WHERE video_id = ?",
                        [[row["video_id"]] for row in allowed],
                        many=True,
                    )
                    logger.info(f"Un-discarded {len(allowed)} video(s).")

    def update(self) -> None:
        super().update()

    def ensure_thumbnails(self) -> None:
        # super().ensure_thumbnails()
        # Remove PYTHON_ERROR_THUMBNAIL errors.
        self.db.modify(
            "DELETE FROM video_error WHERE error = ? AND video_id NOT IN "
            "(SELECT video_id FROM video WHERE "
            "discarded = 1 OR unreadable = 1 OR is_file = 0)",
            [PYTHON_ERROR_THUMBNAIL],
        )
        # Get missing thumbs.
        filename_to_video = {
            row["filename"]: row
            for row in self.db.query(
                "SELECT video_id, filename FROM video "
                "WHERE discarded = 0 AND unreadable = 0 AND is_file = 1"
            )
        }
        existing_filenames = set(filename_to_video)
        existing_thumbs = self.__thumb_mgr.filter(existing_filenames)
        missing_thumbs = sorted(existing_filenames - existing_thumbs)
        # Generate new thumbs.
        thumb_errors = {}
        self.notifier.notify(
            notifications.Message(f"Missing thumbs in SQL: {len(missing_thumbs)}")
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Generate thumbnail filenames as long as tasks
            tasks = [
                (
                    self.notifier,
                    i,
                    filename,
                    AbsolutePath.file_path(tmp_dir, i, "jpg").path,
                )
                for i, filename in enumerate(missing_thumbs)
            ]
            # Generate thumbnail files
            expected_thumbs = {
                filename: thumb_path for _, _, filename, thumb_path in tasks
            }
            raptor = self.__thumb_mgr.raptor
            with Profiler(say("Generate thumbnail files"), self.notifier):
                notify_job_start(
                    self.notifier, raptor.run_thumbnail_task, len(tasks), "thumbnails"
                )
                with Pool() as p:
                    errors = list(p.starmap(raptor.run_thumbnail_task, tasks))
            video_errors = []
            for err in errors:
                if err:
                    del expected_thumbs[err["filename"]]
                    video = filename_to_video[err["filename"]]
                    video_errors.append((video["video_id"], PYTHON_ERROR_THUMBNAIL))
                    video_errors.extend(
                        (video["video_id"], verr) for verr in err["errors"]
                    )
                    thumb_errors[err["filename"]] = err["errors"]
            self.db.modify(
                "INSERT OR IGNORE INTO video_error (video_id, error) VALUES (?, ?)",
                video_errors,
                many=True,
            )
            # Save thumbnails into thumb manager
            with Profiler(say("save thumbnails to db"), self.notifier):
                self.__thumb_mgr.save_existing_thumbnails(expected_thumbs)
            logger.info(f"Thumbnails generated, deleting temp dir {tmp_dir}")
            # Delete thumbnail files (done at context exit)

        if thumb_errors:
            self.notifier.notify(notifications.VideoThumbnailErrors(thumb_errors))
        self._notify_missing_thumbnails()
        self.notifier.notify(notifications.DatabaseUpdated())

    def ensure_miniatures(self, returns=False) -> Optional[List[Miniature]]:
        return super().ensure_miniatures(returns)

    def set_video_similarity(
        self, video_id: int, value: Optional[int], notify=True
    ) -> None:
        super().set_video_similarity(video_id, value, notify)

    def change_video_file_title(self, video_id: int, new_title: str) -> None:
        super().change_video_file_title(video_id, new_title)

    def delete_video(self, video_id: int) -> AbsolutePath:
        return super().delete_video(video_id)

    def reopen(self):
        super().reopen()

    def refresh(self) -> None:
        super().refresh()

    def delete_property_value(self, name: str, values: list) -> None:
        super().delete_property_value(name, values)

    def move_property_value(self, old_name: str, values: list, new_name: str) -> None:
        super().move_property_value(old_name, values, new_name)

    def edit_property_value(
        self, name: str, old_values: list, new_value: object
    ) -> bool:
        return super().edit_property_value(name, old_values, new_value)

    def edit_property_for_videos(
        self,
        video_indices: List[int],
        name: str,
        values_to_add: list,
        values_to_remove: list,
    ) -> None:
        super().edit_property_for_videos(
            video_indices, name, values_to_add, values_to_remove
        )

    def count_property_values(self, video_indices: List[int], name: str) -> List[List]:
        return super().count_property_values(video_indices, name)

    def fill_property_with_terms(self, prop_name: str, only_empty=False) -> None:
        super().fill_property_with_terms(prop_name, only_empty)

    def prop_to_lowercase(self, prop_name) -> None:
        super().prop_to_lowercase(prop_name)

    def prop_to_uppercase(self, prop_name) -> None:
        super().prop_to_uppercase(prop_name)

    def _edit_prop_value(self, prop_name: str, function: Callable[[Any], Any]) -> None:
        super()._edit_prop_value(prop_name, function)

    def move_concatenated_prop_val(
        self, path: list, from_property: str, to_property: str
    ) -> int:
        return super().move_concatenated_prop_val(path, from_property, to_property)

    def to_xspf_playlist(self, video_indices: Iterable[int]) -> AbsolutePath:
        return super().to_xspf_playlist(video_indices)

    def open_containing_folder(self, video_id: int) -> str:
        return super().open_containing_folder(video_id)

    def save(self, on_new_identifiers=False):
        return super().save(on_new_identifiers)

    def __close__(self):
        super().__close__()

    def to_save(self, to_save=True):
        return super().to_save(to_save)

    def register_modified(self, video: Video):
        super().register_modified(video)

    def register_removed(self, video: Video):
        super().register_removed(video)

    def register_replaced(self, new_video: Video, old_video: Video):
        super().register_replaced(new_video, old_video)

    def flush_changes(self):
        super().flush_changes()

    def rename(self, new_name: str) -> None:
        super().rename(new_name)

    def get_name(self):
        return super().get_name()

    def set_date(self, date: Date):
        # super().set_date(date)
        self.db.modify("UPDATE collection SET date_updated = ?", [date.time])

    def get_date(self) -> Date:
        return super().get_date()

    def set_folders(self, folders) -> None:
        super().set_folders(folders)

    def get_folders(self) -> Iterable[AbsolutePath]:
        # return super().get_folders()
        return [
            AbsolutePath(row["source"])
            for row in self.db.query("SELECT source FROM collection_source")
        ]

    def set_predictor(self, prop_name: str, theta: List[float]):
        super().set_predictor(prop_name, theta)

    def get_predictor(self, prop_name):
        return super().get_predictor(prop_name)

    def _get_cached_videos(self, *flags, **forced_flags) -> List[Video]:
        return super()._get_cached_videos(*flags, **forced_flags)

    def count_videos(self, *flags, **forced_flags) -> int:
        return super().count_videos(*flags, **forced_flags)

    def select_videos_fields(
        self, fields: Sequence[str], *flags, **forced_flags
    ) -> Iterable[Dict[str, Any]]:
        return super().select_videos_fields(fields, *flags, **forced_flags)

    def search(
        self, text: str, cond: str = "and", videos: Sequence[int] = None
    ) -> Iterable[int]:
        return super().search(text, cond, videos)

    def sort_video_indices(self, indices: Iterable[int], sorting: VideoSorting):
        return super().sort_video_indices(indices, sorting)

    def has_prop_type(
        self, name, *, with_type=None, multiple=None, with_enum=None, default=None
    ) -> bool:
        return super().has_prop_type(
            name,
            with_type=with_type,
            multiple=multiple,
            with_enum=with_enum,
            default=default,
        )

    def describe_prop_types(self) -> List[dict]:
        return super().describe_prop_types()

    def create_prop_type(
        self,
        name: str,
        prop_type: Union[str, type],
        definition: DefType,
        multiple: bool,
    ) -> None:
        super().create_prop_type(name, prop_type, definition, multiple)

    def remove_prop_type(self, name) -> None:
        super().remove_prop_type(name)

    def rename_prop_type(self, old_name, new_name) -> None:
        super().rename_prop_type(old_name, new_name)

    def convert_prop_to_unique(self, name) -> None:
        super().convert_prop_to_unique(name)

    def convert_prop_to_multiple(self, name) -> None:
        super().convert_prop_to_multiple(name)

    def get_prop_values(self, video_id: int, name: str) -> List[PropValueType]:
        return super().get_prop_values(video_id, name)

    def set_prop_values(
        self, video_id: int, name: str, values: Union[Sequence, Set]
    ) -> None:
        super().set_prop_values(video_id, name, values)

    def merge_prop_values(
        self, video_id: int, name: str, values: Union[Sequence, Set]
    ) -> None:
        super().merge_prop_values(video_id, name, values)

    def validate_prop_values(self, name, values: list) -> List[PropValueType]:
        return super().validate_prop_values(name, values)

    def set_video_properties(self, video_id: int, properties: dict) -> List[str]:
        return super().set_video_properties(video_id, properties)

    def default_prop_unit(self, name):
        return super().default_prop_unit(name)

    def value_is_default(self, name: str, value: list) -> bool:
        return super().value_is_default(name, value)

    def _update_videos_not_found(self, existing_paths: Container[AbsolutePath]):
        # super()._update_videos_not_found(existing_paths)
        rows = self.db.query_all(
            "SELECT video_id, filename FROM video WHERE discarded = 0"
        )
        self.db.modify(
            "UPDATE video SET is_file = ? WHERE video_id = ?",
            [
                (AbsolutePath(row["filename"]) in existing_paths, row["video_id"])
                for row in rows
            ],
            many=True,
        )

    def _notify_properties_modified(self, properties):
        super()._notify_properties_modified(properties)

    def _notify_fields_modified(self, fields: Sequence[str]):
        super()._notify_fields_modified(fields)

    def _notify_filename_modified(self, new_video: Video, old_video: Video):
        super()._notify_filename_modified(new_video, old_video)

    def _notify_missing_thumbnails(self):
        super()._notify_missing_thumbnails()

    def _find_video_paths_for_update(
        self, file_paths: Dict[AbsolutePath, VideoRuntimeInfo]
    ) -> List[str]:
        # return super()._find_video_paths_for_update(file_paths)
        all_file_names = []
        available = {
            AbsolutePath(row["filename"]): row
            for row in self.db.query(
                "SELECT "
                "filename, mtime, file_size, driver_id, "
                "unreadable, audio_codec, audio_bits "
                "FROM video WHERE discarded = 0"
            )
        }
        for file_name, file_info in file_paths.items():
            video: dict = available.get(file_name)
            if (
                video is None
                or file_info.mtime != video["mtime"]
                or file_info.size != video["file_size"]
                or file_info.driver_id != video["driver_id"]
                or self._video_must_be_updated(video)
            ):
                all_file_names.append(file_name.standard_path)
        all_file_names.sort()
        return all_file_names

    @classmethod
    def _video_must_be_updated(cls, video: dict):
        # A video readable with existing audio stream must have valid audio bits
        # return super()._video_must_be_updated(video)
        return (
            not video["unreadable"] and video["audio_codec"] and not video["audio_bits"]
        )

    def get_all_video_indices(self) -> Iterable[int]:
        return super().get_all_video_indices()

    def has_video(self, **fields) -> bool:
        return super().has_video(**fields)

    def get_video_terms(self, video_id: int) -> List[str]:
        return super().get_video_terms(video_id)

    def get_video_filename(self, video_id: int) -> AbsolutePath:
        return super().get_video_filename(video_id)

    def read_video_field(self, video_id: int, field: str):
        return super().read_video_field(video_id, field)

    def write_video_fields(self, video_id: int, **kwargs) -> bool:
        return super().write_video_fields(video_id, **kwargs)

    def write_videos_field(self, indices: Iterable[int], field: str, values: Iterable):
        super().write_videos_field(indices, field, values)

    def fill_videos_field(self, indices: Iterable[int], field: str, value):
        super().fill_videos_field(indices, field, value)

    def add_video_errors(self, video_id: int, *errors: Iterable[str]):
        super().add_video_errors(video_id, *errors)

    def write_new_videos(
        self,
        dictionaries: List[dict],
        runtime_info: Dict[AbsolutePath, VideoRuntimeInfo],
    ) -> None:
        # super().write_new_videos(dictionaries, runtime_info)
        videos: List[Video] = []
        unreadable: List[Video] = []
        for d in dictionaries:
            file_path = AbsolutePath.ensure(d["f"])
            if len(d) == 2:
                video_state = Video.from_keys(
                    filename=file_path.path,
                    file_size=file_path.get_size(),
                    errors=sorted(d["e"]),
                    unreadable=True,
                    database=None,
                )
                unreadable.append(video_state)
            else:
                video_state = Video.from_dict(d, database=None)
            # Video modified, so automatically added to __modified.
            video_state.runtime = runtime_info[file_path]
            videos.append(video_state)

        # Update database.
        video_fields = get_flatten_fields()
        filename_to_video = {video._get("filename"): video for video in videos}
        filename_to_video_id = {
            row["filename"]: row["video_id"]
            for row in self.db.query(
                f"SELECT video_id, filename FROM video "
                f"WHERE filename in ({','.join(['?'] * len(videos))})",
                [video._get("filename") for video in videos],
            )
        }
        new_filenames = [
            filename
            for filename in filename_to_video
            if filename not in filename_to_video_id
        ]
        lines_to_update = [
            (flatten_video(filename_to_video[filename]) + [video_id])
            for filename, video_id in filename_to_video_id.items()
        ]
        lines_to_add = [
            flatten_video(filename_to_video[filename]) for filename in new_filenames
        ]
        self.db.modify(
            f"UPDATE video SET {','.join(f'{field} = ?' for field in video_fields)} "
            f"WHERE video_id = ?",
            lines_to_update,
            many=True,
        )
        self.db.modify(
            f"INSERT INTO video ({','.join(video_fields)}) "
            f"VALUES ({','.join(['?'] * len(video_fields))})",
            lines_to_add,
            many=True,
        )
        filename_to_video_id.update(
            {
                row["filename"]: row["video_id"]
                for row in self.db.query(
                    f"SELECT video_id, filename FROM video "
                    f"WHERE filename in ({','.join(['?'] * len(new_filenames))})",
                    new_filenames,
                )
            }
        )
        assert len(filename_to_video_id) == len(videos)

        video_errors = [
            (filename_to_video_id[filename], error)
            for filename in new_filenames
            for error in sorted(filename_to_video[filename]._get("errors"))
        ]
        video_audio_languages = [
            (filename_to_video_id[filename], "a", lang_code, r)
            for filename in new_filenames
            for r, lang_code in enumerate(
                filename_to_video[filename]._get("audio_languages")
            )
        ]
        video_subtitle_languages = [
            (filename_to_video_id[filename], "s", lang_code, r)
            for filename in new_filenames
            for r, lang_code in enumerate(
                filename_to_video[filename]._get("subtitle_languages")
            )
        ]
        video_texts = [
            (
                filename_to_video_id[filename],
                get_video_text(filename_to_video[filename], []),
            )
            for filename in new_filenames
        ]

        self.db.modify(
            "INSERT INTO video_error (video_id, error) VALUES (?, ?)",
            video_errors,
            many=True,
        )
        self.db.modify(
            "INSERT INTO video_language (video_id, stream, lang_code, rank) "
            "VALUES (?, ?, ?, ?)",
            video_audio_languages + video_subtitle_languages,
            many=True,
        )
        self.db.modify(
            "INSERT INTO video_text (video_id, content) VALUES(?, ?)",
            video_texts,
            many=True,
        )

        if unreadable:
            self.notifier.notify(
                notifications.VideoInfoErrors(
                    {
                        video_state.filename: video_state.errors
                        for video_state in unreadable
                    }
                )
            )

    def change_video_entry_filename(
        self, video_id: int, path: AbsolutePath
    ) -> AbsolutePath:
        return super().change_video_entry_filename(video_id, path)

    def delete_video_entry(self, video_id: int):
        super().delete_video_entry(video_id)

    def move_video_entry(self, from_id, to_id) -> None:
        super().move_video_entry(from_id, to_id)

    def confirm_unique_moves(self) -> int:
        return super().confirm_unique_moves()

    def open_video(self, video_id: int) -> None:
        super().open_video(video_id)

    def describe_videos(self, video_indices: Sequence[int], with_moves=False):
        return super().describe_videos(video_indices, with_moves)

    def get_common_fields(self, video_indices: Iterable[int]) -> dict:
        return super().get_common_fields(video_indices)

    def old_get_thumbnail_path(self, video: Video):
        return super().old_get_thumbnail_path(video)

    def get_thumbnail_base64(self, filename: AbsolutePath) -> str:
        return super().get_thumbnail_base64(filename)

    def get_thumbnail_blob(self, filename: AbsolutePath):
        return super().get_thumbnail_blob(filename)

    def has_thumbnail(self, filename: AbsolutePath) -> bool:
        return super().has_thumbnail(filename)

    def save_thumbnail(self, filename: AbsolutePath) -> Optional[dict]:
        return super().save_thumbnail(filename)
