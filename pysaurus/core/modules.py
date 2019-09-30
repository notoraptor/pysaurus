import base64
import os
import sys
from html.parser import HTMLParser

from PIL import Image
from moviepy.video.io.VideoFileClip import VideoFileClip

from pysaurus.core.exceptions import NoVideoClip
from pysaurus.core.functions import whirlpool_hash


class HTMLStripper(HTMLParser):
    """ HTML parser class to remove HTML tags from a string.
        Example:
            text = HTMLStripper.strip(text)
        Reference: (2018/09/24) https://stackoverflow.com/a/925630
    """

    def error(self, message):
        pass

    def __init__(self):
        """ Constructor """
        super(HTMLStripper, self).__init__(convert_charrefs=True)
        self.fed = []

    def handle_data(self, data):
        """ Split text to blank delimiters and store text pieces. """
        self.fed.extend(data.split())

    def get_data(self):
        """ Return filtered text pieces, joined with space.
            Each spaces sequence should contain only 1 space in returned text.
        """
        return ' '.join(self.fed)

    @classmethod
    def strip(cls, msg):
        """ Remove HTML tags from given message and return stripped message. """
        html_stripper = HTMLStripper()
        html_stripper.feed(msg)
        return html_stripper.get_data()


class System:

    @staticmethod
    def is_windows():
        return sys.platform == 'win32'

    @staticmethod
    def is_linux():
        return sys.platform == 'linux'

    @staticmethod
    def is_mac():
        return sys.platform == 'darwin'

    @staticmethod
    def platform():
        return sys.platform

    @staticmethod
    def is_case_insensitive(folder='.'):
        base_name = os.path.join(folder, 'tmp')
        count = 0
        while True:
            test_name = '%s%d' % (base_name, count)
            if os.path.exists(test_name):
                count += 1
            else:
                break
        with open(test_name, 'w+'):
            is_insensitive = os.path.exists(test_name.upper())
        os.unlink(test_name)
        return is_insensitive


class VideoClipping:

    @staticmethod
    def get_video_duration(path):
        return VideoFileClip(path).duration

    @staticmethod
    def video_clip(path, time_start=0, clip_seconds=10, unique_id=None):
        assert isinstance(time_start, int) and time_start >= 0
        assert isinstance(clip_seconds, int) and clip_seconds > 0
        clip = VideoFileClip(path)
        time_end = time_start + clip_seconds
        if time_start > clip.duration:
            time_start = clip.duration
        if time_end > clip.duration:
            time_end = clip.duration
        if time_start - time_end == 0:
            raise NoVideoClip()
        if unique_id is None:
            path = os.path.abspath(path)
            unique_id = whirlpool_hash(path)
        output_name = '%s_%s_%s.mp4' % (unique_id, time_start, clip_seconds)
        print('Taking clip from %s to %s sec in: %s' % (time_start, time_end, output_name))
        sub_clip = clip.subclip(time_start, time_end)
        sub_clip.write_videofile(output_name)
        sub_clip.close()
        clip.close()
        del clip
        del sub_clip
        return output_name

    @staticmethod
    def video_clip_to_base64(path, time_start=0, clip_seconds=10, unique_id=None):
        output_path = VideoClipping.video_clip(path, time_start, clip_seconds, unique_id)
        with open(output_path, 'rb') as file:
            content = file.read()
        encoded = base64.b64encode(content)
        print(len(encoded) / len(content))
        os.unlink(output_path)
        return encoded


class ImageUtils:
    IMAGE_RGB_MODE = 'RGB'
    IMAGE_GRAY_MODE = 'L'
    DEFAULT_THUMBNAIL_SIZE = (32, 32)

    @staticmethod
    def __save_image(mode, size, data, name):
        output_image = Image.new(mode=mode, size=size, color=0)
        output_image.putdata(data)
        output_image.save(name)
        return output_image

    @staticmethod
    def open_rgb_image(file_name):
        image = Image.open(file_name)
        if image.mode != ImageUtils.IMAGE_RGB_MODE:
            image = image.convert(ImageUtils.IMAGE_RGB_MODE)
        return image

    @staticmethod
    def save_gray_image(width, height, data, name):
        # Data must be a list of gray values in [0; 255].
        return ImageUtils.__save_image(ImageUtils.IMAGE_GRAY_MODE, (width, height), data, name)

    @staticmethod
    def save_rgb_image(width, height, data, name):
        # Data must be a list of triples (r, g, b), each in [0; 255].
        return ImageUtils.__save_image(ImageUtils.IMAGE_RGB_MODE, (width, height), data, name)
