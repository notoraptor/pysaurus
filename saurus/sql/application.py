from pathlib import Path

from pysaurus.core.components import AbsolutePath
from saurus.language import say
from saurus.sql import data
from saurus.sql.video_database import VideoDatabase


class Application:
    def __init__(self):
        self.app_name = "Pysaurus"
        self.home_dir = AbsolutePath(str(Path.home()))
        self.app_dir = AbsolutePath.join(self.home_dir, f".{self.app_name}").mkdir()
        self.db_path = AbsolutePath.join(self.app_dir, f"databases.db")
        self.lang_dir = AbsolutePath.join(self.app_dir, "languages").mkdir()

        self.db = VideoDatabase(self.db_path.path)
        row = self.db.query_one("SELECT application_id, lang FROM application")
        self.application_id = row[0]
        self.lang = row[1]

        say.set_language(self.lang)
        say.set_folder(self.lang_dir)

    def list_collections(self):
        return [
            row[0]
            for row in self.db.query("SELECT name FROM collection ORDER BY name ASC")
        ]

    def open_collection(self, name: str):
        r_col = self.db.query_one("SELECT * FROM collection WHERE name = ?", [name])
        collection_id = r_col["collection_id"]
        sources = [
            row[0]
            for row in self.db.query_all(
                "SELECT source FROM collection_source WHERE collection_id = ?",
                [collection_id],
            )
        ]
        properties = {}
        videos = {}
        for r_prop in self.db.query_all(
            "SELECT * FROM property WHERE collection_id = ?", [collection_id]
        ):
            property_id = r_prop["property_id"]
            prop = data.Property(
                property_id=property_id,
                name=r_prop["name"],
                type=r_prop["type"],
                default_value=r_prop["default_value"],
                enumeration=[
                    row[0]
                    for row in self.db.query(
                        "SELECT enum_value FROM property_enumeration "
                        "WHERE property_id = ? ORDER BY rank ASC",
                        [property_id],
                    )
                ],
            )
            properties[prop.name] = prop
        for r_vid in self.db.query_all(
            "SELECT "
            "v.video_id, v.filename, v.file_size, v.mtime, v.driver_id, v.is_file, "
            "v.readable, v.audio_bit_rate, v.audio_codec, v.audio_codec_description, "
            "v.bit_depth, v.channels, v.container_format, v.device_name, v.duration, "
            "v.duration_time_base, v.frame_rate_den, v.frame_rate_num, v.height, "
            "v.meta_title, v.sample_rate, v.video_codec, v.video_codec_description, "
            "v.width, c.thumb_name, c.has_thumbnail, c.similarity_id "
            "FROM video AS v JOIN collection_to_video AS c ON v.video_id = c.video_id "
            "WHERE c.collection_id = ?",
            [collection_id],
        ):
            video_id = r_vid[0]
            video = data.Video(
                video_id=video_id,
                filename=r_vid[1],
                file_size=r_vid[2],
                mtime=r_vid[3],
                driver_id=r_vid[4],
                is_file=r_vid[5],
                readable=r_vid[6],
                audio_bit_rate=r_vid[7],
                audio_codec=r_vid[8],
                audio_codec_description=r_vid[9],
                bit_depth=r_vid[10],
                channels=r_vid[11],
                container_format=r_vid[12],
                device_name=r_vid[13],
                duration=r_vid[14],
                duration_time_base=r_vid[15],
                frame_rate_den=r_vid[16],
                frame_rate_num=r_vid[17],
                height=r_vid[18],
                meta_title=r_vid[19],
                sample_rate=r_vid[20],
                video_codec=r_vid[21],
                video_codec_description=r_vid[22],
                width=r_vid[23],
                thumb_name=r_vid[24],
                has_thumbnail=r_vid[25],
                similarity_id=r_vid[26],
                errors=[
                    row[0]
                    for row in self.db.query_all(
                        "SELECT error FROM video_error "
                        "WHERE video_id = ? ORDER BY error ASC",
                        [video_id],
                    )
                ],
                audio_languages=[
                    row[0]
                    for row in self.db.query_all(
                        "SELECT lang_code FROM video_language "
                        "WHERE video_id = ? AND stream = ? ORDER BY rank ASC",
                        (video_id, "audio"),
                    )
                ],
                subtitle_languages=[
                    row[0]
                    for row in self.db.query_all(
                        "SELECT lang_code FROM video_language "
                        "WHERE video_id = ? AND stream = ? ORDER BY rank ASC",
                        (video_id, "subtitle"),
                    )
                ],
                properties={
                    prop.name: [
                        row[0]
                        for row in self.db.query_all (
                            "SELECT property_value FROM video_property_value "
                            "WHERE property_id = ? AND video_id = ?",
                            (prop.property_id, video_id),
                        )
                    ]
                    for prop in properties.values()
                },
            )
            videos[video.filename] = video
        return data.Collection(
            collection_id=collection_id,
            name=r_col["name"],
            date_updated=r_col["date_updated"],
            miniature_pixel_distance_radius=r_col["miniature_pixel_distance_radius"],
            miniature_group_min_size=r_col["miniature_group_min_size"],
            sources=sources,
            properties=properties,
            videos=videos,
        )
