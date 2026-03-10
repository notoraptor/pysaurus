from typing import Sequence


class SourceFlag:
    __slots__ = ("flag", "children")

    def __init__(self, flag: str):
        self.flag = flag
        self.children: dict[str, SourceFlag] = {}

    def __str__(self):
        return f"{self.flag}{sorted(self.children.values()) or ''}"

    __repr__ = __str__

    def __eq__(self, other):
        return self.flag == other.flag and self.children == other.children

    def __lt__(self, other):
        return self.flag < other.flag


class SourceDef:
    __slots__ = ("children", "sources")
    __SOURCE_FLAG_CLASS__ = SourceFlag

    def __init__(self, sources: Sequence[Sequence[str]]):
        self.sources: set[Sequence[str]] = set()
        self.children: dict[str, SourceFlag] = {}
        for source in sources:
            self.add(source)

    def __str__(self):
        return str(sorted(self.children.values()))

    def __len__(self):
        return len(self.sources)

    def __eq__(self, other):
        return self.children == other.children

    def add(self, source: Sequence[str]) -> bool:
        added = False
        children = self.children
        for flag in source:
            if flag not in children:
                children[flag] = self.__SOURCE_FLAG_CLASS__(flag)
                added = True
            children = children[flag].children
        if added:
            self.sources.add(tuple(source))
        return added
