import logging
from typing import Collection, Dict, Iterable, List, Sequence, Tuple, Union

from pysaurus.application import exceptions
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
from saurus.sql.pysaurus_connection import PysaurusConnection
from saurus.sql.saurus_provider import SaurusProvider
from saurus.sql.sql_old.video_entry import VideoEntry

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

    def get_videos(
        self,
        *,
        include: Sequence[str] = None,
        with_moves: bool = False,
        where: dict = None,
    ) -> List[dict]:
        pass

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
        pass

    def delete_video_entry(self, video_id: int) -> None:
        pass

    def write_videos_field(self, indices: Iterable[int], field: str, values: Iterable):
        pass

    def write_new_videos(
        self,
        video_entries: List[VideoEntry],
        runtime_info: Dict[AbsolutePath, VideoRuntimeInfo],
    ) -> None:
        pass

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

    def get_unique_moves(self) -> List[Tuple[int, int]]:
        pass

    def get_common_fields(self, video_indices):
        pass

    def _insert_new_thumbnails(self, filename_to_thumb_name: Dict[str, str]) -> None:
        filename_to_video_id = {
            row[0]: row[1]
            for row in self.db.query(
                f"SELECT filename, video_id FROM video "
                f"WHERE filename IN ({','.join(['?'] * len(filename_to_thumb_name))})",
                list(filename_to_thumb_name.keys())
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
