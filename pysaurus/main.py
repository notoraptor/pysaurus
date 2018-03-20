import os
from datetime import datetime

from pysaurus.new_video import NewVideo
from pysaurus.utils.profiling import Profiling
from pysaurus.utils.symbols import PACKAGE_DIR, is_valid_video_filename
from pysaurus.video import Video


def test_videos():
    t1 = datetime.now()
    video_path = os.path.abspath(os.path.join(PACKAGE_DIR, 'res', 'video'))
    assert os.path.exists(video_path) and os.path.isdir(video_path)
    videos = {}
    by_format = {}
    for filename in os.listdir(video_path):
        if is_valid_video_filename(filename):
            file_path = os.path.join(video_path, filename)
            try:
                video = NewVideo(file_path)
                videos[video.absolute_path] = video
                characteristics = video.characteristics
                if characteristics not in by_format:
                    by_format[characteristics] = set()
                by_format[characteristics].add(video)
            except Exception:
                print('Unable to get info from file', file_path)
                raise
    t2 = datetime.now()
    print(len(videos), len(by_format))
    print(Profiling(t1, t2))


def test_one_video():
    t1 = datetime.now()
    video_file_path = os.path.abspath(os.path.join(PACKAGE_DIR, 'res', 'video', 'Lion.ogv'))
    video = NewVideo(video_file_path)
    t2 = datetime.now()
    parsed = Video.parse(str(video))
    assert parsed.absolute_path == video.absolute_path
    assert parsed.characteristics == video.characteristics
    print(video.video_id)
    print(video.thumbnail)
    print(Profiling(t1, t2))
    from pysaurus.utils.ffmpeg_backend import create_thumbnail
    print(create_thumbnail(video, '.'))
    print(video.container_format, video.audio_codec, video.video_codec)


def test_database():
    from pysaurus.database import Database
    database = Database(db_folder_name='C:\\Users\\notoraptor\\Downloads\\pdb',
                        video_folder_names=[
                            'C:\\donnees\\programmation\\git\\pysaurus\\res\\video'
                        ])
    database.save()


# test_videos()
# test_one_video()
test_database()
