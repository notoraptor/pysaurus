from dataclasses import dataclass

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.properties.properties import PropType
from pysaurus.video.video_search_context import VideoSearchContext


@dataclass(slots=True)
class DatabaseContext:
    name: str
    folders: list[AbsolutePath]
    prop_types: list[PropType]
    view: VideoSearchContext

    def json(self):
        return {
            "database": {
                "name": self.name,
                "folders": [str(path) for path in self.folders],
            },
            "prop_types": [pt.to_dict() for pt in self.prop_types],
            **self.view.json(),
        }
