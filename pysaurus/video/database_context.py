from dataclasses import dataclass

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.video.video_search_context import VideoSearchContext


@dataclass(slots=True)
class DatabaseContext:
    name: str
    folders: list[AbsolutePath]
    prop_types: list[dict]
    view: VideoSearchContext

    def json(self):
        return {
            "database": {
                "name": self.name,
                "folders": [str(path) for path in self.folders],
            },
            "prop_types": self.prop_types,
            **self.view.json(),
        }
