from typing import Dict, Sequence

from pysaurus.video.video import Video


class _SourceFlag:
    __slots__ = ("flag", "children")

    def __init__(self, flag: str):
        self.flag = flag
        self.children: Dict[str, _SourceFlag] = {}

    def __str__(self):
        return f"{self.flag}{sorted(self.children.values()) or ''}"

    __repr__ = __str__

    def __lt__(self, other):
        return self.flag < other.flag

    def contains_flag(self, flag):
        return self.flag == flag or any(
            child.contains_flag(flag) for child in self.children.values()
        )

    def contains_video(self, video: Video):
        return getattr(video, self.flag) and (
            not self.children
            or any(child.contains_video(video) for child in self.children.values())
        )

    def has_path_without(self, flag):
        return self.flag != flag and (
            not self.children
            or any(child.has_path_without(flag) for child in self.children.values())
        )


class SourceDef:
    __slots__ = ("children",)

    def __init__(self, sources: Sequence[Sequence[str]]):
        self.children: Dict[str, _SourceFlag] = {}
        for source in sources:
            self.add(source)

    def __str__(self):
        return str(sorted(self.children.values()))

    def add(self, source: Sequence[str]):
        children = self.children
        for flag in source:
            if flag not in children:
                children[flag] = _SourceFlag(flag)
            children = children[flag].children

    def contains_flag(self, flag: str) -> bool:
        return any(child.contains_flag(flag) for child in self.children.values())

    def contains_video(self, video: Video) -> bool:
        return any(child.contains_video(video) for child in self.children.values())

    def has_source_without(self, flag):
        return any(child.has_path_without(flag) for child in self.children.values())
