from other.saurus.sql import data
from other.saurus.sql.application import Application as NewApp
from pysaurus.application.application import Application as OldApp
from pysaurus.core.profiling import Profiler
from pysaurus.database.properties import PropType
from pysaurus.database.video import Video


def old_to_new_prop(old_p: PropType) -> data.Property:
    return data.Property(
        name=old_p.name,
        type=old_p.type.__name__,
        default_value=None if old_p.multiple else old_p.default,
        enumeration=old_p.definition if old_p.is_enum() else [],
    )


def old_to_new_video(video) -> data.Video:
    return (
        data.Video(
            video_id=video.video_id,
            filename=video.filename.path,
            file_size=video.file_size,
            mtime=video.runtime.mtime,
            driver_id=(video.runtime.driver_id or 0),
            is_file=video.runtime.is_file,
            readable=video.readable,
            audio_bit_rate=video.audio_bit_rate,
            audio_codec=str(video.audio_codec),
            audio_codec_description=str(video.audio_codec_description),
            bit_depth=video.bit_depth,
            channels=video.channels,
            container_format=str(video.container_format),
            device_name=str(video.device_name),
            duration=video.duration,
            duration_time_base=video.duration_time_base,
            frame_rate_den=video.frame_rate_den,
            frame_rate_num=video.frame_rate_num,
            height=video.height,
            meta_title=str(video.meta_title),
            sample_rate=video.sample_rate,
            video_codec=str(video.video_codec),
            video_codec_description=str(video.video_codec_description),
            width=video.width,
            errors=video.errors,
            audio_languages=video.audio_languages,
            subtitle_languages=video.subtitle_languages,
            thumb_name=video.thumb_name,
            has_thumbnail=video.runtime.has_thumbnail,
            similarity_id=video.similarity_id,
            properties={
                k: v if isinstance(v, list) else [v]
                for k, v in video.properties.items()
            },
        )
        if isinstance(video, Video)
        else data.Video(
            video_id=video.video_id,
            filename=video.filename.path,
            file_size=video.file_size,
            mtime=video.runtime.mtime,
            driver_id=video.runtime.driver_id,
            is_file=video.runtime.is_file,
            readable=video.readable,
            errors=video.errors,
            has_thumbnail=video.runtime.has_thumbnail,
            thumb_name=video.get_thumb_name(),
        )
    )


def main():
    report = []
    old_app = OldApp()
    with Profiler("Adding databases"):
        for database_path in old_app.get_database_paths():
            db = old_app.open_database(database_path)
            info = (database_path.title, db.nb_entries)
            report.append(info)
            print("[loading]", *info)
            new_app = NewApp()
            collection = data.Collection(
                name=db.folder.title,
                date_updated=db.date.time,
                miniature_pixel_distance_radius=db.settings.miniature_pixel_distance_radius,
                miniature_group_min_size=db.settings.miniature_group_min_size,
                sources=[source.path for source in db.video_folders],
                properties={
                    prop.name: old_to_new_prop(prop) for prop in db.get_prop_types()
                },
                videos={
                    video.filename.path: old_to_new_video(video)
                    for video in db.query({})
                },
            )
            with Profiler(f"Adding: {database_path.title}"):
                new_app.db.add_collection(collection=collection)
    print()
    nb_total_entries = 0
    for (title, count) in report:
        print(title, count)
        nb_total_entries += count
    print("TOTAL", nb_total_entries)


if __name__ == "__main__":
    main()
