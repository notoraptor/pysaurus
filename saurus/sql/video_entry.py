from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Sequence

from pysaurus.video import VideoRuntimeInfo


@dataclass
class VideoEntry:
    # table columns: constant data
    filename: str
    video_id: int = None
    file_size: int = 0
    unreadable: bool = False
    audio_bit_rate: int = 0
    audio_bits: int = 0
    audio_codec: str = ""
    audio_codec_description: str = ""
    bit_depth: int = 0
    channels: int = 0
    container_format: str = ""
    device_name: str = ""
    duration: float = 0.0
    duration_time_base: int = 0
    frame_rate_den: int = 0
    frame_rate_num: int = 0
    height: int = 0
    meta_title: str = ""
    sample_rate: int = 0
    video_codec: str = ""
    video_codec_description: str = ""
    width: int = 0
    # table columns: runtime frozen data
    mtime: float = 0.0
    driver_id: int = None
    is_file: bool = False
    discarded: float = False
    # related data
    errors: Sequence[str] = field(default_factory=list)
    audio_languages: Sequence[str] = field(default_factory=list)
    subtitle_languages: Sequence[str] = field(default_factory=list)
    # collection data
    date_entry_modified: float = None
    date_entry_opened: float = None
    similarity_id: int = None
    properties: Dict[str, Sequence[str]] = field(default_factory=dict)

    def to_formatted_dict(self):
        output = asdict(self)
        del output["mtime"]
        del output["driver_id"]
        del output["is_file"]
        return output

    def to_table(
        self, for_update=False, runtime_info: VideoRuntimeInfo = None
    ) -> Dict[str, Any]:
        output = asdict(self)
        del output["errors"]
        del output["audio_languages"]
        del output["subtitle_languages"]
        del output["properties"]
        del output["date_entry_opened"]
        del output["similarity_id"]
        if not for_update:
            del output["video_id"]
        if runtime_info:
            output["mtime"] = runtime_info.mtime
            output["driver_id"] = runtime_info.driver_id
            output["is_file"] = runtime_info.is_file
        return output
