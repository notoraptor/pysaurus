import os
import subprocess
import ujson as json

from pysaurus.video import Video


def get_json_info(video_path):
    command = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_error', '-show_format', '-show_streams',
        str(video_path)
    ]
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    std_out, std_err = p.communicate()
    if std_err:
        raise Exception(std_err)
    return json.loads(std_out)


def create_thumbnail(video: Video, output_folder, output_format='jpg'):
    output_file_path = os.path.abspath(os.path.join(output_folder, '%s.%s' % (video.title, output_format)))
    command = [
        'ffmpeg', '-y', '-ss', int(video.duration / 2),
        str(video.absolute_path),
        '-vframes 1', output_file_path
    ]
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    if not os.path.exists(output_file_path):
        raise Exception(output_file_path)
    return output_file_path
