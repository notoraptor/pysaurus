from tqdm import tqdm

from saurus.sql import data
from saurus.sql.database import Database


class VideoDatabase(Database):
    __slots__ = ()

    def add_collection(self, *, collection: data.Collection):
        # Collection
        if self.select_id_from_values(
            "collection", "collection_id", name=collection.name
        ):
            raise RuntimeError(f"Collection already exists: {collection.name}")
        collection.collection_id = self.insert(
            "collection",
            name=collection.name,
            date_updated=collection.date_updated,
            miniature_pixel_distance_radius=collection.miniature_pixel_distance_radius,
            miniature_group_min_size=collection.miniature_group_min_size,
        )
        # Collection sources
        for source in collection.sources:
            self.insert(
                "collection_source",
                collection_id=collection.collection_id,
                source=source,
            )
        # Properties
        for prop in collection.properties.values():
            if self.select_id_from_values(
                "property",
                "property_id",
                collection_id=collection.collection_id,
                name=prop.name,
            ):
                raise RuntimeError(
                    f"Property already exists: {collection.name}/{prop.name}"
                )
            property_id = self.insert(
                "property",
                collection_id=collection.collection_id,
                name=prop.name,
                type=prop.type,
                default_value=prop.default_value,
            )
            prop.property_id = property_id
            # property enumeration
            for i, value in enumerate(prop.enumeration):
                self.insert(
                    "property_enumeration",
                    property_id=property_id,
                    enum_value=value,
                    rank=i,
                )
        # Videos
        videos = list(collection.videos.values())
        for index_video in tqdm(range(len(videos))):
            self.add_video(video=videos[index_video], collection=collection)

    def add_video(self, *, video: data.Video, collection: data.Collection):
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
        self.insert(
            "collection_to_video",
            collection_id=collection.collection_id,
            video_id=video_id,
            thumb_name=video.thumb_name,
            has_thumbnail=video.has_thumbnail,
            similarity_id=video.similarity_id,
        )
        # video property value
        for prop_name, prop_vals in video.properties.items():
            prop = collection.properties[prop_name]
            for value in prop_vals:
                self.insert(
                    "video_property_value",
                    video_id=video_id,
                    property_id=prop.property_id,
                    property_value=value,
                )
