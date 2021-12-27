from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence, Dict

from tqdm import tqdm

from pysaurus.core.components import AbsolutePath
from saurus.language import say
from saurus.sql.database import Database


@dataclass
class Property:
    name: str
    type: str
    default_value: str = None
    enumeration: Sequence[str] = field(default_factory=list)
    property_id: int = None

    multiple = property(lambda self: self.default_value is None)


@dataclass
class Video:
    video_id: int
    filename: str
    file_size: int = 0
    mtime: float = 0.0
    driver_id: int = 0
    is_file: bool = False
    readable: bool = False
    audio_bit_rate: int = 0
    audio_codec: str = ""
    audio_codec_description: str = ""
    bit_depth: int = 0
    channels: int = 2
    container_format: str = ""
    device_name: str = ""
    duration: int = 0
    duration_time_base: int = 0
    frame_rate_den: int = 0
    frame_rate_num: int = 0
    height: int = 0
    meta_title: str = ""
    sample_rate: int = 0
    video_codec: str = ""
    video_codec_description: str = ""
    width: int = 0

    errors: Sequence[str] = field(default_factory=list)
    audio_languages: Sequence[str] = field(default_factory=list)
    subtitle_languages: Sequence[str] = field(default_factory=list)

    thumb_name: str = ""
    has_thumbnail: bool = False
    similarity_id: int = None
    properties: Dict[str, Sequence[str]] = field(default_factory=dict)

    def table_columns(self):
        return {
            key: getattr(self, key)
            for key in (
                # "video_id",
                "filename",
                "file_size",
                "mtime",
                "driver_id",
                "is_file",
                "readable",
                "audio_bit_rate",
                "audio_codec",
                "audio_codec_description",
                "bit_depth",
                "channels",
                "container_format",
                "device_name",
                "duration",
                "duration_time_base",
                "frame_rate_den",
                "frame_rate_num",
                "height",
                "meta_title",
                "sample_rate",
                "video_codec",
                "video_codec_description",
                "width",
            )
        }


@dataclass
class Collection:
    name: str
    date_updated: float
    miniature_pixel_distance_radius: int = 6
    miniature_group_min_size: int = 0
    sources: Sequence[str] = field(default_factory=list)
    properties: Dict[str, Property] = field(default_factory=dict)
    videos: Dict[str, Video] = field(default_factory=dict)


class Application:
    def __init__(self, lang: str = "english"):
        self.lang = lang

        self.app_name = "Pysaurus"
        self.home_dir = AbsolutePath(str(Path.home()))
        self.app_dir = AbsolutePath.join(self.home_dir, f".{self.app_name}").mkdir()
        self.db_path = AbsolutePath.join(self.app_dir, f"databases.db")
        self.lang_dir = AbsolutePath.join(self.app_dir, "languages").mkdir()

        self.db = Database(self.db_path.path)
        say.set_language(self.lang)
        say.set_folder(self.lang_dir)

    def save(self, collection: Collection):
        # Collection
        if self.db.select_id_from_values(
            "collection", "collection_id", name=collection.name
        ):
            raise RuntimeError(f"Collection already exists: {collection.name}")
        collection_id = self.db.insert(
            "collection",
            name=collection.name,
            date_updated=collection.date_updated,
            miniature_pixel_distance_radius=collection.miniature_pixel_distance_radius,
            miniature_group_min_size=collection.miniature_group_min_size,
        )
        # Collection sources
        for source in collection.sources:
            self.db.insert(
                "collection_source", collection_id=collection_id, source=source
            )
        # Properties
        for prop in collection.properties.values():
            if self.db.select_id_from_values(
                "property",
                "property_id",
                collection_id=collection_id,
                name=prop.name,
            ):
                raise RuntimeError(
                    f"Property already exists: {collection.name}/{prop.name}"
                )
            property_id = self.db.insert(
                "property",
                collection_id=collection_id,
                name=prop.name,
                type=prop.type,
                default_value=prop.default_value,
            )
            prop.property_id = property_id
            # property enumeration
            for i, value in enumerate(prop.enumeration):
                self.db.insert(
                    "property_enumeration",
                    property_id=property_id,
                    enum_value=value,
                    rank=i,
                )
        # Videos
        videos = list(collection.videos.values())
        for index_video in tqdm(range(len(videos))):
            video = videos[index_video]
            video_id = self.db.select_id_from_values(
                "video", "video_id", filename=video.filename
            ) or self.db.insert("video", **video.table_columns())
            # video errors
            for error in video.errors:
                self.db.insert_or_ignore("video_error", video_id=video_id, error=error)
            # video language
            for i, lang in enumerate(video.audio_languages):
                self.db.insert_or_ignore(
                    "video_language",
                    video_id=video_id,
                    stream="audio",
                    lang_code=lang,
                    rank=i,
                )
            for i, lang in enumerate(video.subtitle_languages):
                self.db.insert_or_ignore(
                    "video_language",
                    video_id=video_id,
                    stream="subtitle",
                    lang_code=lang,
                    rank=i,
                )
            # collection to video
            self.db.insert(
                "collection_to_video",
                collection_id=collection_id,
                video_id=video_id,
                thumb_name=video.thumb_name,
                has_thumbnail=video.has_thumbnail,
                similarity_id=video.similarity_id,
            )
            # video property value
            for prop_name, prop_vals in video.properties.items():
                prop = collection.properties[prop_name]
                for value in prop_vals:
                    self.db.insert(
                        "video_property_value",
                        video_id=video_id,
                        property_id=prop.property_id,
                        property_value=value,
                    )
