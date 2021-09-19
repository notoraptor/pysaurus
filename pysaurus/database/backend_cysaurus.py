from pysaurus.core.components import AbsolutePath
from pysaurus.core.custom_json_parser import parse_json
from pysaurus.database import video_raptor


def backend_video_infos(job):
    file_names, job_id, database_folder, job_notifier = job
    list_file_path = AbsolutePath.file_path(database_folder, str(job_id), "list")
    json_file_path = AbsolutePath.file_path(database_folder, str(job_id), "json")

    with open(list_file_path.path, "wb") as file:
        for file_name in file_names:
            file.write(("%s\n" % file_name).encode())

    count = video_raptor.job_video_to_json((
        list_file_path.path,
        json_file_path.path,
        len(file_names),
        job_id,
        job_notifier,
    ))
    assert json_file_path.isfile()
    arr = parse_json(json_file_path)
    assert len(arr) == count
    list_file_path.delete()
    json_file_path.delete()
    return arr


def backend_video_thumbnails(job):
    videos_data, job_id, db_folder, thumb_folder, job_notifier = job
    list_file_path = AbsolutePath.file_path(db_folder, job_id, "thumbnails.list")
    json_file_path = AbsolutePath.file_path(db_folder, job_id, "thumbnails.json")

    with open(list_file_path.path, "wb") as file:
        for file_path, thumb_name in videos_data:
            file.write(f"{file_path}\t{thumb_folder}\t{thumb_name}\t\n".encode())

    nb_loaded = video_raptor.job_video_thumbnails_to_json((
        list_file_path.path,
        json_file_path.path,
        len(videos_data),
        job_id,
        job_notifier,
    ))
    assert json_file_path.isfile()
    arr = parse_json(json_file_path)
    assert arr[-1] is None
    arr.pop()
    assert nb_loaded + len(arr) == len(videos_data)
    list_file_path.delete()
    json_file_path.delete()
    return arr
