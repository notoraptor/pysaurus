import subprocess
import ujson as json

from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.exceptions import FFmpegException, FFprobeException
from pysaurus.video import Video


def get_json_info(video_path):
    command = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_error', '-show_format', '-show_streams', video_path]
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    std_out, std_err = p.communicate()
    if std_err:
        raise FFprobeException(std_err)
    return json.loads(std_out)


def create_thumbnail(video: Video, output_folder: AbsolutePath, output_title: str, output_extension: str = 'jpg'):
    output_file_path = AbsolutePath.new_file_path(output_folder, output_title, output_extension)
    std_out, std_err = subprocess.Popen(
        ['ffmpeg', '-y', '-ss', str(int(video.duration / 2)), '-i', video.absolute_path.path,
         '-vframes', '1', output_file_path.path], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if not output_file_path.exists():
        raise FFmpegException('\r\n%s\r\n%s' % (output_file_path, std_err.decode('utf-8')))
    return output_file_path


def get_ffprobe_command(video_path: AbsolutePath, output_name):
    return ('ffprobe -v quiet -print_format json -show_error -show_format -show_streams "%s" >> %s.json'
            % (video_path, output_name))
