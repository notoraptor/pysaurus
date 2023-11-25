import logging
import operator
from collections import defaultdict
from typing import Collection, Dict, Iterable, List, Sequence, Tuple, Union

from pysaurus.application import exceptions
from pysaurus.core import notifications
from pysaurus.core.components import AbsolutePath, Date
from pysaurus.core.functions import string_to_pieces
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.path_tree import PathTree
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.db_settings import DbSettings
from pysaurus.properties.properties import PropRawType, PropTypeValidator, PropUnitType
from pysaurus.video.lazy_video_runtime_info import (
    LazyVideoRuntimeInfo as VideoRuntimeInfo,
)
from pysaurus.video.video_features import VideoFeatures
from saurus.sql.pysaurus_connection import PysaurusConnection
from saurus.sql.saurus_provider import SaurusProvider
from saurus.sql.sql_useful_constants import (
    FORMATTED_VIDEO_TABLE_FIELDS,
    WRITABLE_FIELDS,
)
from saurus.sql.video_entry import VideoEntry
from saurus.sql.video_parser import SQLVideoWrapper, VideoParser

logger = logging.getLogger(__name__)


class PysaurusCollection(AbstractDatabase):
    __slots__ = ("db",)

    def __init__(self, path, folders=None, notifier=DEFAULT_NOTIFIER):
        super().__init__(path, SaurusProvider(self), notifier)
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
        self.db.modify(
            "UPDATE video SET discarded = ? WHERE video_id = ?",
            [
                (
                    not folders_tree.in_folders(AbsolutePath(video["filename"])),
                    video["video_id"],
                )
                for video in videos
            ],
            many=True,
        )
        self.db.modify(
            "INSERT OR IGNORE INTO collection_source (source) VALUES (?)",
            [(path.path,) for path in folders],
            many=True,
        )

    def get_predictor(self, prop_name: str) -> List[float]:
        logger.error("get_predictor not yet implemented.")
        raise NotImplementedError()

    def set_predictor(self, prop_name: str, theta: List[float]) -> None:
        logger.error("set_predictor not yet implemented.")
        raise NotImplementedError()

    def get_prop_values(self, video_id: int, name: str) -> Collection[PropUnitType]:
        (prop_desc,) = self.get_prop_types(name=name)
        pt = PropTypeValidator(prop_desc)
        return pt.from_strings(
            [
                row["val"]
                for row in self.db.query(
                    "SELECT pv.property_value AS val "
                    "FROM video_property_value AS pv "
                    "JOIN property AS p "
                    "ON p.property_id = pv.property_id "
                    "WHERE p.name = ? AND pv.video_id = ?",
                    [name, video_id],
                )
            ]
        )

    def update_prop_values(
        self, video_id: int, name: str, values: Collection, *, merge=False
    ):
        (prop_desc,) = self.get_prop_types(name=name)
        pt = PropTypeValidator(prop_desc)
        values = pt.instantiate(values)
        property_id = pt.property_id

        if values:
            if pt.multiple and merge:
                self.db.modify(
                    "INSERT OR IGNORE INTO video_property_value "
                    "(video_id, property_id, property_value) VALUES (?, ?, ?)",
                    [(video_id, property_id, value) for value in values],
                    many=True,
                )
            else:  # replace anyway
                self.db.modify(
                    "DELETE FROM video_property_value "
                    "WHERE video_id = ? AND property_id = ?",
                    [video_id, property_id],
                )
                self.db.modify(
                    "INSERT INTO video_property_value "
                    "(video_id, property_id, property_value) VALUES (?, ?, ?)",
                    [(video_id, property_id, value) for value in values],
                    many=True,
                )
        elif not merge:  # replace with empty => remove
            self.db.modify(
                "DELETE FROM video_property_value "
                "WHERE video_id = ? AND property_id = ?",
                [video_id, property_id],
            )

    def get_prop_types(
        self, *, name=None, with_type=None, multiple=None, with_enum=None, default=None
    ) -> List[dict]:
        where = []
        parameters = []
        if name is not None:
            where.append("name = ?")
            parameters.append(name)
        if with_type is not None:
            where.append("type = ?")
            parameters.append(with_type.__name__)
        if multiple is not None:
            where.append("multiple = ?")
            parameters.append(int(bool(multiple)))
        where_clause = " AND ".join(where)
        clause = "SELECT property_id, name, type, multiple FROM property"
        if where_clause:
            clause += f" WHERE {where_clause}"

        ret = []
        for row in self.db.query_all(clause, parameters):
            enumeration = [
                res["enum_value"]
                for res in self.db.query(
                    "SELECT enum_value FROM property_enumeration "
                    "WHERE property_id = ? ORDER BY rank ASC",
                    [row["property_id"]],
                )
            ]
            if (
                with_enum is None
                or (len(enumeration) > 1 and set(enumeration) == set(with_enum))
            ) and (default is None or enumeration[0] == default):
                ret.append(
                    {
                        "property_id": row["property_id"],
                        "name": row["name"],
                        "type": row["type"],
                        "multiple": row["multiple"],
                        "defaultValue": enumeration[0],
                        "enumeration": enumeration if len(enumeration) > 1 else None,
                    }
                )

        return ret

    def create_prop_type(
        self,
        name: str,
        prop_type: Union[str, type],
        definition: PropRawType,
        multiple: bool,
    ) -> None:
        prop_desc = PropTypeValidator.define(
            name, prop_type, definition, multiple, describe=True
        )
        if self.get_prop_types(name=prop_desc["name"]):
            raise exceptions.PropertyAlreadyExists(prop_desc["name"])
        property_id = self.db.modify(
            "INSERT INTO property (name, type, multiple) VALUES (?, ?, ?)",
            [prop_desc["name"], prop_desc["type"], int(prop_desc["multiple"])],
        )
        self.db.modify(
            "INSERT INTO property_enumeration (property_id, enum_value, rank) "
            "VALUES (?, ?, ?)",
            [
                (property_id, value, rank)
                for rank, value in enumerate(
                    prop_desc["enumeration"] or [prop_desc["defaultValue"]]
                )
            ],
            many=True,
        )

    def remove_prop_type(self, name: str):
        self.db.modify("DELETE FROM property WHERE name = ?", [name])

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
        parser = VideoParser()
        args = dict(parser(key, value) for key, value in (where or {}).items())
        selection = [
            (key, args.pop(key)) for key in ("video_id", "filename") if key in args
        ]
        parameters = []
        queries_where = []
        if selection:
            qs = []
            for key, values in selection:
                qs.append(
                    (
                        f"v.{key} = ?"
                        if len(values) == 1
                        else f"v.{key} IN ({', '.join(['?'] * len(values))})"
                    )
                )
                parameters.extend(values)
            queries_where.append(f"({' OR '.join(qs)})")
        args_keys = list(args.keys())
        queries_where.extend(f"v.{key} = ?" for key in args_keys)
        parameters.extend(args[key] for key in args_keys)

        query = (
            f"SELECT {FORMATTED_VIDEO_TABLE_FIELDS}, t.thumbnail AS thumbnail, "
            f"IIF(LENGTH(t.thumbnail), 1, 0) AS with_thumbnails "
            f"FROM video AS v LEFT JOIN video_thumbnail AS t "
            f"ON v.video_id = t.video_id"
        )
        if queries_where:
            query += f" WHERE {' AND '.join(queries_where)}"
        videos = [SQLVideoWrapper(row) for row in self.db.query(query, parameters)]

        video_indices = [video.data["video_id"] for video in videos]
        placeholders = ", ".join(["?"] * len(video_indices))

        errors = defaultdict(list)
        languages = {"a": defaultdict(list), "s": defaultdict(list)}
        properties = defaultdict(dict)
        json_properties = {}
        with_errors = include is None or "errors" in include
        with_audio_languages = include is None or "audio_languages" in include
        with_subtitle_languages = include is None or "subtitle_languages" in include
        with_properties = include is None or "json_properties" in include
        if with_errors:
            for row in self.db.query(
                f"SELECT video_id, error FROM video_error "
                f"WHERE video_id IN ({placeholders})",
                video_indices,
            ):
                errors[row[0]].append(row[1])
        if with_audio_languages or with_subtitle_languages:
            for row in self.db.query(
                f"SELECT stream, video_id, lang_code FROM video_language "
                f"WHERE video_id IN ({placeholders}) "
                f"ORDER BY stream ASC, video_id ASC, rank ASC",
                video_indices,
            ):
                languages[row[0]][row[1]].append(row[2])
        if with_properties:
            prop_types: Dict[int, PropTypeValidator] = {
                desc["property_id"]: PropTypeValidator(desc)
                for desc in self.get_prop_types()
            }
            for row in self.db.query(
                f"SELECT video_id, property_id, property_value "
                f"FROM video_property_value WHERE video_id IN ({placeholders})",
                video_indices,
            ):
                properties[row[0]].setdefault(row[1], []).append(row[2])
            json_properties = {
                video_id: {
                    prop_types[property_id]
                    .name: prop_types[property_id]
                    .plain_from_strings(values)
                    for property_id, values in raw_properties.items()
                }
                for video_id, raw_properties in properties.items()
            }

        if with_errors:
            for video in videos:
                video.errors = errors.get(video.video_id, [])
        if with_audio_languages:
            for video in videos:
                video.audio_languages = languages["a"].get(video.video_id, [])
        if with_subtitle_languages:
            for video in videos:
                video.subtitle_languages = languages["s"].get(video.video_id, [])
        if with_properties:
            for video in videos:
                video.properties = json_properties.get(video.video_id, {})

        if include is None:
            # Return all, use with_moves.
            return [video.json(with_moves) for video in videos]
        else:
            # Use include, ignore with_moves
            fields = include or ("video_id",)
            return [{key: getattr(video, key) for key in fields} for video in videos]

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

    def add_video_errors(self, video_id: int, *errors: Iterable[str]) -> None:
        self.db.modify(
            "INSERT OR IGNORE INTO video_error (video_id, error) VALUES (?, ?)",
            [(video_id, error) for error in errors],
            many=True,
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
            f"SELECT v.video_id, group_concat(v.property_value, ';') "
            f"FROM video_property_value AS v JOIN property AS p "
            f"ON v.property_id = p.property_id "
            f"WHERE p.type = 'str' GROUP BY v.video_id "
            f"HAVING v.video_id IN ({','.join(['?'] * len(entries))})",
            [entry.video_id for entry in entries],
        ):
            entry = entry_map[row[0]]
            text = f"{entry.filename};{entry.meta_title};{row[1]}"
            texts.append((entry.video_id, text))
        self.db.modify_many(
            "INSERT INTO video_text (video_id, content) VALUES (?, ?)", texts
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
WHERE unreadable = 0 
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
            assert not_found and found
            for id_not_found in not_found:
                yield id_not_found, found

    def get_common_fields(self, video_indices: Iterable[int]) -> dict:
        return VideoFeatures.get_common_fields(
            self.get_videos(where={"video_id": video_indices}),
            getfield=operator.getitem,
        )

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
        self.db.modify(
            "INSERT OR REPLACE INTO video_thumbnail (video_id, thumbnail) VALUES (?, ?)",
            (
                (
                    filename_to_video_id[filename],
                    AbsolutePath(thumb_path).read_binary_file(),
                )
                for filename, thumb_path in filename_to_thumb_name.items()
            ),
            many=True,
        )
