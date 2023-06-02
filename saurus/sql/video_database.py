import os

from tqdm import tqdm

from saurus.sql import data
from saurus.sql.database import Database


class VideoDatabase(Database):
    __slots__ = ()
    DATABASE_SCRIPT_FILE = os.path.join(os.path.dirname(__file__), "database.sql")

    def __init__(self, path: str):
        super().__init__(self.DATABASE_SCRIPT_FILE, path)

    def add_collection(self, *, collection: data.Collection):
        # Collection
        collection.collection_id = self.select_id_from_values(
            "collection", "collection_id", name=collection.name
        ) or self.insert(
            "collection",
            name=collection.name,
            date_updated=collection.date_updated,
            miniature_pixel_distance_radius=collection.miniature_pixel_dst_radius,
            miniature_group_min_size=collection.miniature_group_min_size,
        )
        # Collection sources
        for source in collection.sources:
            self.insert_or_ignore(
                "collection_source",
                collection_id=collection.collection_id,
                source=source,
            )
        # Properties
        for prop in collection.properties.values():
            self.add_property(prop=prop, collection=collection)
        # Videos
        for video in tqdm(list(collection.videos.values())):
            self.add_video(video=video, collection=collection)

    def add_property(self, *, prop: data.Property, collection: data.Collection):
        # Will update prop.property_id
        property_id = self.select_id_from_values(
            "property",
            "property_id",
            collection_id=collection.collection_id,
            name=prop.name,
            type=prop.type,
            default_value=prop.default_value,
        ) or self.insert(
            "property",
            collection_id=collection.collection_id,
            name=prop.name,
            type=prop.type,
            default_value=prop.default_value,
        )
        # property enumeration
        for i, value in enumerate(prop.enumeration):
            self.insert_or_ignore(
                "property_enumeration",
                property_id=property_id,
                enum_value=value,
                rank=i,
            )
        prop.property_id = property_id

    def add_video(self, *, video: data.Video, collection: data.Collection):
        # Will update video.video_id
        video_id = self.select_id_from_values(
            "video", "video_id", filename=video.filename
        ) or self.insert(
            "video",
            filename=video.filename,
            file_size=video.file_size,
            mtime=video.mtime,
            driver_id=video.driver_id,
            is_file=video.is_file,
            readable=video.readable,
            audio_bit_rate=video.audio_bit_rate,
            audio_codec=video.audio_codec,
            audio_codec_description=video.audio_codec_description,
            bit_depth=video.bit_depth,
            channels=video.channels,
            container_format=video.container_format,
            device_name=video.device_name,
            duration=video.duration,
            duration_time_base=video.duration_time_base,
            frame_rate_den=video.frame_rate_den,
            frame_rate_num=video.frame_rate_num,
            height=video.height,
            meta_title=video.meta_title,
            sample_rate=video.sample_rate,
            video_codec=video.video_codec,
            video_codec_description=video.video_codec_description,
            width=video.width,
        )
        # video errors
        for error in video.errors:
            self.insert_or_ignore("video_error", video_id=video_id, error=error)
        # video language
        for i, lang in enumerate(video.audio_languages):
            self.insert_or_ignore(
                "video_language",
                video_id=video_id,
                stream="audio",
                lang_code=lang,
                rank=i,
            )
        for i, lang in enumerate(video.subtitle_languages):
            self.insert_or_ignore(
                "video_language",
                video_id=video_id,
                stream="subtitle",
                lang_code=lang,
                rank=i,
            )
        # collection to video
        self.insert_or_ignore(
            "collection_to_video",
            collection_id=collection.collection_id,
            video_id=video_id,
            thumb_name=video.thumb_name,
            similarity_id=video.similarity_id,
        )
        # video property value
        for prop_name, prop_vals in video.properties.items():
            prop = collection.properties[prop_name]
            for value in prop_vals:
                self.insert_or_ignore(
                    "video_property_value",
                    video_id=video_id,
                    property_id=prop.property_id,
                    property_value=value,
                )
        video.video_id = video_id
