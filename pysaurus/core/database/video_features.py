import base64
from io import BytesIO

from pysaurus.core.constants import THUMBNAIL_EXTENSION
from pysaurus.core.database.video import Video
from pysaurus.core.functions import to_json_value, class_get_public_attributes
from pysaurus.core.modules import ImageUtils, VideoClipping


class VideoFeatures:
    @staticmethod
    def thumbnail_to_base64(self: Video):
        thumb_path = self.thumbnail_path
        if not thumb_path.isfile():
            return None
        image = ImageUtils.open_rgb_image(thumb_path.path)
        buffered = BytesIO()
        image.save(buffered, format=THUMBNAIL_EXTENSION)
        image_string = base64.b64encode(buffered.getvalue())
        return image_string

    @staticmethod
    def clip_to_base64(self: Video, start, length):
        return VideoClipping.video_clip_to_base64(
            path=self.filename.path,
            time_start=start,
            clip_seconds=length,
            unique_id=self.ensure_thumbnail_name(),
        )

    @staticmethod
    def to_json(self, **kwargs):
        js = {
            field: to_json_value(getattr(self, field))
            for field in class_get_public_attributes(type(self))
        }
        js.update(kwargs)
        return js
