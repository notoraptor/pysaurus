import logging
from typing import Collection, Dict, Iterable, List, Sequence, Tuple, Union

from pysaurus.application import exceptions
from pysaurus.core import notifications
from pysaurus.core.components import AbsolutePath, Date
from pysaurus.core.functions import string_to_pieces
from pysaurus.core.path_tree import PathTree
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.db_settings import DbSettings
from pysaurus.properties.properties import PropRawType, PropTypeValidator, PropUnitType
from pysaurus.video.lazy_video_runtime_info import (
    LazyVideoRuntimeInfo as VideoRuntimeInfo,
)
from saurus.sql.prop_type_search import prop_type_search
from saurus.sql.pysaurus_connection import PysaurusConnection
from saurus.sql.saurus_provider import SaurusProvider
from saurus.sql.sql_useful_constants import WRITABLE_FIELDS
from saurus.sql.sql_video_wrapper import SQLVideoWrapper
from saurus.sql.video_entry import VideoEntry
from saurus.sql.video_mega_search import video_mega_search

logger = logging.getLogger(__name__)

PREFIX = {"thumbnail": "", "with_thumbnails": ""}


def get_sql_prefix(field: str) -> str:
    return PREFIX.get(field, "v.")


class PysaurusCollection(AbstractDatabase):
    __slots__ = ("db",)

    def __init__(self, path, folders=None):
        super().__init__(path, SaurusProvider(self))
        self.db = PysaurusConnection(self.ways.db_sql_path.path)
        if folders:
            self.set_folders(
                set(self.get_folders())
                | {AbsolutePath.ensure(folder) for folder in folders}
            )

    def set_date(self, date: Date):
        self.db.modify("UPDATE collection SET date_updated = ?", [date.time])

    def get_settings(self) -> DbSettings:
        row = self.db.query_one(
            "SELECT miniature_pixel_distance_radius, miniature_group_min_size "
            "FROM collection"
        )
        return DbSettings.from_keys(
            miniature_pixel_distance_radius=row["miniature_pixel_distance_radius"],
            miniature_group_min_size=row["miniature_group_min_size"],
        )

    def get_folders(self) -> Iterable[AbsolutePath]:
        return [
            AbsolutePath(row["source"])
            for row in self.db.query("SELECT source FROM collection_source")
        ]

    def set_folders(self, folders) -> None:
        folders = sorted(AbsolutePath.ensure(folder) for folder in folders)
        if folders == sorted(self.get_folders()):
            return
        folders_tree = PathTree(folders)
        videos = self.db.query_all("SELECT video_id, filename FROM video")
        self.db.modify_many(
            "UPDATE video SET discarded = ? WHERE video_id = ?",
            [
                (
                    not folders_tree.in_folders(AbsolutePath(video["filename"])),
                    video["video_id"],
                )
                for video in videos
            ],
        )
        self.db.modify_many(
            "INSERT OR IGNORE INTO collection_source (source) VALUES (?)",
            [(path.path,) for path in folders],
        )

    def get_predictor(self, prop_name: str) -> List[float]:
        logger.error("get_predictor not yet implemented.")
        raise NotImplementedError()

    def set_predictor(self, prop_name: str, theta: List[float]) -> None:
        logger.error("set_predictor not yet implemented.")
        raise NotImplementedError()

    def get_all_prop_values(
        self, name: str, indices: List[int] = ()
    ) -> Dict[int, Collection[PropUnitType]]:
        (prop_desc,) = self.get_prop_types(name=name)
        pt = PropTypeValidator(prop_desc)
        output = {}
        for row in self.db.query(
            "SELECT pv.video_id, pv.property_value "
            "FROM video_property_value AS pv "
            "JOIN property AS p "
            "ON pv.property_id = p.property_id "
            "WHERE p.name = ?"
            + (
                f" AND pv.video_id IN ({','.join(['?'] * len(indices))})"
                if indices
                else ""
            ),
            [name] + indices,
        ):
            output.setdefault(row[0], []).append(pt.from_string(row[1]))
        return output

    def set_video_prop_values(
        self, name: str, updates: Dict[int, Collection[PropUnitType]], merge=False
    ):
        (prop_desc,) = self.get_prop_types(name=name)
        pt = PropTypeValidator(prop_desc)
        video_indices = list(updates.keys())
        placeholders_string = ",".join(["?"] * len(video_indices))
        for video_id in video_indices:
            updates[video_id] = pt.instantiate(updates[video_id])

        property_id = pt.property_id
        if not merge or not pt.multiple:
            self.db.modify(
                f"DELETE FROM video_property_value "
                f"WHERE property_id = ? "
                f"AND video_id IN ({placeholders_string})",
                [property_id] + video_indices,
            )
        self.db.modify_many(
            "INSERT OR IGNORE INTO video_property_value "
            "(video_id, property_id, property_value) VALUES (?, ?, ?)",
            (
                (video_id, property_id, value)
                for video_id, values in updates.items()
                for value in values
            ),
        )
        if pt.type is str:
            new_texts = self.db.query_all(
                f"SELECT v.video_id, v.filename, v.meta_title, t.property_text "
                f"FROM video AS v JOIN video_property_text AS t "
                f"ON v.video_id = t.video_id "
                f"WHERE v.video_id IN ({placeholders_string})",
                video_indices,
            )
            self.db.modify(
                f"DELETE FROM video_text WHERE video_id IN ({placeholders_string})",
                video_indices,
            )
            self.db.modify_many(
                "INSERT INTO video_text "
                "(video_id, filename, meta_title, properties) VALUES (?,?,?,?)",
                new_texts,
            )

    def set_video_properties(
        self, video_id: int, properties: dict, merge=False
    ) -> None:
        if not properties:
            return
        props: Dict[str, PropTypeValidator] = {
            prop_desc["name"]: PropTypeValidator(prop_desc)
            for prop_desc in self.get_prop_types()
        }
        validated_properties = {
            name: props[name].as_sql(props[name].instantiate(values))
            for name, values in properties.items()
        }
        string_properties = [name for name in properties if props[name].type is str]
        unique_prop_indices = [
            props[name].property_id for name in properties if not props[name].multiple
        ]
        if not merge:
            self.db.modify(
                f"DELETE FROM video_property_value WHERE video_id = ? "
                f"AND property_id IN ({','.join(['?'] * len(properties))})",
                [video_id] + [props[name].property_id for name in properties],
            )
        elif unique_prop_indices:
            self.db.modify(
                f"DELETE FROM video_property_value HWERE video_id = ? "
                f"AND property_id IN ({','.join(['?'] * len(unique_prop_indices))})",
                [video_id] + unique_prop_indices,
            )
        self.db.modify_many(
            "INSERT OR IGNORE INTO video_property_value "
            "(video_id, property_id, property_value) VALUES (?, ?, ?)",
            (
                (video_id, props[name].property_id, value)
                for name, values in validated_properties.items()
                for value in values
            ),
        )
        if string_properties:
            (new_texts,) = self.db.query_all(
                "SELECT v.video_id, v.filename, v.meta_title, t.property_text "
                "FROM video AS v JOIN video_property_text AS t "
                "ON v.video_id = t.video_id "
                "WHERE v.video_id = ?",
                [video_id],
            )
            self.db.modify("DELETE FROM video_text WHERE video_id = ?", [video_id])
            self.db.modify(
                "INSERT INTO video_text "
                "(video_id, filename, meta_title, properties) VALUES (?,?,?,?)",
                new_texts,
            )

    def get_prop_types(
        self, *, name=None, with_type=None, multiple=None, with_enum=None, default=None
    ) -> List[dict]:
        return prop_type_search(
            self.db,
            name=name,
            with_type=with_type,
            multiple=multiple,
            with_enum=with_enum,
            default=default,
        )

    def create_prop_type(
        self,
        name: str,
        prop_type: Union[str, type],
        definition: PropRawType,
        multiple: bool,
    ) -> None:
        prop_def = PropTypeValidator.define(
            name, prop_type, definition, multiple, describe=True
        )
        if self.get_prop_types(name=prop_def["name"]):
            raise exceptions.PropertyAlreadyExists(prop_def["name"])
        property_id = self.db.modify(
            "INSERT INTO property (name, type, multiple) VALUES (?, ?, ?)",
            [prop_def["name"], prop_def["type"], int(prop_def["multiple"])],
        )
        self.db.modify_many(
            "INSERT INTO property_enumeration (property_id, enum_value, rank) "
            "VALUES (?, ?, ?)",
            [
                (property_id, value, rank)
                for rank, value in enumerate(
                    prop_def["enumeration"] or [prop_def["default"]]
                )
            ],
        )

    def remove_prop_type(self, name: str):
        video_indices = []
        pt = self.db.query_one(
            "SELECT property_id, type FROM property WHERE name = ?", [name]
        )
        if pt["type"] == "str":
            video_indices = [
                row[0]
                for row in self.db.query(
                    "SELECT DISTINCT video_id FROM video_property_value "
                    "WHERE property_id = ?",
                    [pt["property_id"]],
                )
            ]

        self.db.modify("DELETE FROM property WHERE name = ?", [name])

        if video_indices:
            updates = self.db.query_all(
                f"SELECT property_text, video_id FROM video_property_text "
                f"WHERE video_id IN ({','.join(['?'] * len(video_indices))})",
                video_indices,
            )
            # Seems irrelevant:
            # updated_indices = [row[1] for row in updates]
            # self.db.modify(
            #     f"UPDATE video_text SET properties = '' "
            #     f"WHERE video_id NOT IN ({','.join(['?'] * len(updated_indices))})",
            #     updated_indices,
            # )
            self.db.modify_many(
                "UPDATE video_text SET properties = ? WHERE video_id = ?", updates
            )

    def rename_prop_type(self, old_name, new_name):
        if self.get_prop_types(name=old_name):
            if self.get_prop_types(name=new_name):
                raise exceptions.PropertyAlreadyExists(new_name)
            self.db.modify(
                "UPDATE property SET name = ? WHERE name = ?", [new_name, old_name]
            )

    def convert_prop_multiplicity(self, name: str, multiple: bool) -> None:
        props = self.get_prop_types(name=name)
        if props:
            (prop_desc,) = props
            if bool(prop_desc["multiple"]) is bool(multiple):
                raise exceptions.PropertyAlreadyMultiple(name, multiple)
            if not multiple:
                res = self.db.query_one(
                    "SELECT COUNT(p.property_value) AS nb, v.filename AS filename "
                    "FROM video_property_value AS p "
                    "JOIN video AS v ON p.video_id = v.video_id "
                    "WHERE p.property_id = ? "
                    "GROUP BY p.video_id ORDER BY nb DESC LIMIT 1",
                    [prop_desc["property_id"]],
                )
                if res["nb"] > 1:
                    raise exceptions.PropertyToUniqueError(name, res["filename"])
            self.db.modify(
                "UPDATE property SET multiple = ? WHERE name = ?",
                [int(bool(multiple)), name],
            )

    x = SQLVideoWrapper

    def get_videos(
        self,
        *,
        include: Sequence[str] = None,
        with_moves: bool = False,
        where: dict = None,
    ) -> List[dict]:
        # where = where or {}
        # where["discarded"] = where.get("discarded", False)
        return video_mega_search(
            self.db, include=include, with_moves=with_moves, where=where
        )

    def get_video_terms(self, video_id: int) -> List[str]:
        video = self.db.query_one(
            "SELECT filename, meta_title FROM video WHERE video_id = ?", [video_id]
        )
        prop_vals = [
            row[0]
            for row in self.db.query(
                "SELECT v.property_value FROM video_property_value AS v "
                "JOIN property AS p ON v.property_id = p.property_id "
                "WHERE v.video_id = ? AND p.type = ?",
                [video_id, "str"],
            )
        ]
        term_sources = [video[0], video[1]] + prop_vals
        all_str = " ".join(term_sources)
        t_all_str = string_to_pieces(all_str)
        t_all_str_low = string_to_pieces(all_str.lower())
        return t_all_str if t_all_str == t_all_str_low else (t_all_str + t_all_str_low)

    def get_all_video_terms(self) -> Dict[int, List[str]]:
        output = {}
        for row in self.db.query(
            """
            SELECT v.video_id, v.filename || ' ' || v.meta_title || ' ' || COALESCE(pv.property_text, '')
            FROM video AS v
            LEFT JOIN video_property_text AS pv ON v.video_id = pv.video_id
"""
        ):
            t_all_str = string_to_pieces(row[1])
            t_all_str_low = string_to_pieces(row[1].lower())
            output[row[0]] = (
                t_all_str if t_all_str == t_all_str_low else (t_all_str + t_all_str_low)
            )
        return output

    def add_video_errors(self, video_id: int, *errors: Iterable[str]) -> None:
        self.db.modify_many(
            "INSERT OR IGNORE INTO video_error (video_id, error) VALUES (?, ?)",
            [(video_id, error) for error in errors],
        )

    def change_video_entry_filename(
        self, video_id: int, path: AbsolutePath
    ) -> AbsolutePath:
        path = AbsolutePath.ensure(path)
        assert path.isfile()
        (video,) = self.get_videos(
            include=["filename"], where={"video_id": video_id, "unreadable": False}
        )
        old_filename = AbsolutePath.ensure(video["filename"])
        assert old_filename != path
        self.db.modify(
            "UPDATE video SET filename = ? WHERE video_id = ?", [path.path, video_id]
        )
        self._notify_fields_modified(
            (
                "title",
                "title_numeric",
                "file_title",
                "file_title_numeric",
                "filename_numeric",
                "disk",
                "filename",
            )
        )
        return old_filename

    def delete_video_entry(self, video_id: int) -> None:
        self.db.modify("DELETE FROM video WHERE video_id = ?", [video_id])
        self.provider.delete(video_id)
        self._notify_fields_modified(["move_id", "quality"])

    def write_videos_field(self, indices: Iterable[int], field: str, values: Iterable):
        self.db.modify_many(
            f"UPDATE video SET {WRITABLE_FIELDS[field]} = ? WHERE video_id = ?",
            zip(values, indices),
        )

    def write_new_videos(
        self,
        video_entries: List[VideoEntry],
        runtime_info: Dict[AbsolutePath, VideoRuntimeInfo],
    ) -> None:
        entry_with_new_meta_titles: List[VideoEntry] = []
        entry_map: Dict[str, VideoEntry] = {
            entry.filename: entry for entry in video_entries
        }
        assert len(entry_map) == len(video_entries)
        filenames = list(entry_map.keys())
        for row in self.db.query(
            f"SELECT video_id, filename, meta_title FROM video "
            f"WHERE filename IN ({','.join(['?'] * len(filenames))})",
            filenames,
        ):
            entry = entry_map[row[1]]
            entry.video_id = row[0]
            if entry.meta_title != row[2]:
                entry_with_new_meta_titles.append(entry)
        old_entries = [entry for entry in video_entries if entry.video_id is not None]
        new_entries = [entry for entry in video_entries if entry.video_id is None]
        self._update_video_entries(old_entries, runtime_info)
        self._add_pure_new_entries(new_entries, runtime_info)
        self._update_video_texts(entry_with_new_meta_titles + new_entries)
        unreadable = {
            entry.filename: entry.errors for entry in video_entries if entry.unreadable
        }
        if unreadable:
            self.notifier.notify(notifications.VideoInfoErrors(unreadable))

    def _update_video_entries(
        self,
        entries: List[VideoEntry],
        runtime_info: Dict[AbsolutePath, VideoRuntimeInfo],
    ):
        if not entries:
            return
        dicts = [
            entry.to_table(True, runtime_info[AbsolutePath(entry.filename)])
            for entry in entries
        ]
        fields = list(dicts[0].keys())
        self.db.modify_many(
            f"UPDATE video "
            f"SET {','.join(f'{field} = :{field}' for field in fields)} "
            f"WHERE video_id = :video_id",
            dicts,
        )

        to_add_errors = []
        to_add_languages = []
        for entry in entries:
            to_add_errors.extend((entry.video_id, error) for error in entry.errors)
            to_add_languages.extend(
                (entry.video_id, "a", code, rank)
                for rank, code in enumerate(entry.audio_languages)
            )
            to_add_languages.extend(
                (entry.video_id, "s", code, rank)
                for rank, code in enumerate(entry.subtitle_languages)
            )

        indice_parameters = [[entry.video_id] for entry in entries]
        self.db.modify_many(
            "DELETE FROM video_error WHERE video_id = ?", indice_parameters
        )
        self.db.modify_many(
            "DELETE FROM video_language WHERE video_id = ?", indice_parameters
        )
        self.db.modify_many(
            "INSERT INTO video_error (video_id, error) VALUES (?, ?)", to_add_errors
        )
        self.db.modify_many(
            "INSERT INTO video_language (video_id, stream, lang_code, rank) "
            "VALUES (?, ?, ?, ?)",
            to_add_languages,
        )

    def _add_pure_new_entries(
        self,
        entries: List[VideoEntry],
        runtime_info: Dict[AbsolutePath, VideoRuntimeInfo],
    ):
        if not entries:
            return
        dicts = [
            entry.to_table(False, runtime_info[AbsolutePath(entry.filename)])
            for entry in entries
        ]
        fields = list(dicts[0].keys())
        self.db.modify_many(
            f"INSERT INTO video ({','.join(fields)}) "
            f"VALUES ({','.join(f':{field}' for field in fields)})",
            dicts,
        )
        entry_map = {entry.filename: entry for entry in entries}
        assert len(entry_map) == len(entries)
        nb_indices = 0
        for row in self.db.query(
            f"SELECT filename, video_id FROM video "
            f"WHERE filename IN ({','.join(['?'] * len(entries))})",
            [entry.filename for entry in entries],
        ):
            entry_map[row[0]].video_id = row[1]
            nb_indices += 1
        assert nb_indices == len(entries)
        errors = [
            (entry.video_id, error) for entry in entries for error in entry.errors
        ]
        audio_languages = [
            (entry.video_id, "a", code, rank)
            for entry in entries
            for rank, code in enumerate(entry.audio_languages)
        ]
        subtitle_languages = [
            (entry.video_id, "s", code, rank)
            for entry in entries
            for rank, code in enumerate(entry.subtitle_languages)
        ]
        self.db.modify_many(
            "INSERT INTO video_error (video_id, error) VALUES (?, ?)", errors
        )
        self.db.modify_many(
            "INSERT INTO video_language (video_id, stream, lang_code, rank) "
            "VALUES (?, ?, ?, ?)",
            audio_languages + subtitle_languages,
        )

    def _update_video_texts(self, entries: List[VideoEntry]):
        entry_map = {entry.video_id: entry for entry in entries}
        assert len(entry_map) == len(entries)
        texts = []
        for row in self.db.query(
            f"SELECT video_id, property_text FROM video_property_text "
            f"WHERE video_id IN ({','.join(['?'] * len(entries))})",
            [entry.video_id for entry in entries],
        ):
            entry = entry_map[row[0]]
            texts.append((entry.video_id, entry.filename, entry.meta_title, row[1]))
        self.db.modify_many(
            "INSERT OR REPLACE INTO video_text "
            "(video_id, filename, meta_title, properties) VALUES (?, ?, ?, ?)",
            texts,
        )

    def open_video(self, video_id):
        AbsolutePath(
            self.db.query_one(
                "SELECT filename FROM video WHERE video_id = ?", [video_id]
            )["filename"]
        ).open()
        self.db.modify(
            "UPDATE video SET date_entry_opened = ? WHERE video_id = ?",
            [Date.now().time, video_id],
        )
        self._notify_fields_modified(["date_entry_opened"])

    def get_moves(self) -> Iterable[Tuple[int, List[dict]]]:
        for row in self.db.query(
            """
SELECT group_concat(video_id || '-' || is_file || '-' || hex(filename))
FROM video
WHERE unreadable = 0 AND discarded = 0
GROUP BY file_size, duration, COALESCE(NULLIF(duration_time_base, 0), 1)
HAVING COUNT(video_id) > 1 AND SUM(is_file) < COUNT(video_id);
                """
        ):
            not_found = []
            found = []
            for piece in row[0].split(","):
                str_video_id, str_is_file, str_hex_filename = piece.split("-")
                video_id = int(str_video_id)
                if int(str_is_file):
                    found.append(
                        {
                            "video_id": video_id,
                            "filename": AbsolutePath(
                                bytes.fromhex(str_hex_filename).decode("utf-8")
                            ).standard_path,
                        }
                    )
                else:
                    not_found.append(video_id)
            assert not_found and found, (not_found, found)
            for id_not_found in not_found:
                yield id_not_found, found

    def _insert_new_thumbnails(self, filename_to_thumb_name: Dict[str, str]) -> None:
        filename_to_video_id = {
            row[0]: row[1]
            for row in self.db.query(
                f"SELECT filename, video_id FROM video "
                f"WHERE filename IN ({','.join(['?'] * len(filename_to_thumb_name))})",
                list(filename_to_thumb_name.keys()),
            )
        }
        assert len(filename_to_video_id) == len(filename_to_thumb_name)
        self.db.modify_many(
            "INSERT OR REPLACE INTO video_thumbnail (video_id, thumbnail) VALUES (?, ?)",
            (
                (
                    filename_to_video_id[filename],
                    AbsolutePath(thumb_path).read_binary_file(),
                )
                for filename, thumb_path in filename_to_thumb_name.items()
            ),
        )

    def delete_property_value(self, name: str, values: list) -> List[int]:
        if not values:
            return []
        (prop_desc,) = self.get_prop_types(name=name)
        modified = [
            row["video_id"]
            for row in self.db.query(
                f"SELECT video_id FROM video_property_value "
                f"WHERE property_id = ? "
                f"AND property_value IN ({','.join(['?'] * len(values))})",
                [prop_desc["property_id"]] + values,
            )
        ]
        self.db.modify(
            f"DELETE FROM video_property_value "
            f"WHERE property_id = ? "
            f"AND property_value IN ({','.join(['?'] * len(values))})",
            [prop_desc["property_id"]] + values,
        )
        self._notify_properties_modified([name])
        return modified
