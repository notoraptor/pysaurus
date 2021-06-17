import os
from typing import Dict

from pysaurus.core.components import AbsolutePath


class PathTreeNode:
    __slots__ = ("name", "children")

    def __init__(self, name: str):
        self.name = name
        self.children = {}  # type: Dict[str, PathTreeNode]


class PathTree(PathTreeNode):
    __slots__ = ()

    def __init__(self, folders=()):
        super().__init__("")
        for folder in folders:
            self.add(folder)

    def add(self, path: AbsolutePath):
        children = self.children
        for piece in path.standard_path.split(os.sep):
            if piece in children:
                node = children[piece]
            else:
                node = PathTreeNode(piece)
                children[node.name] = node
            children = node.children

    def in_folders(self, path: AbsolutePath):
        pieces = path.standard_path.split(os.sep)
        children = self.children
        for i, piece in enumerate(pieces):
            if piece in children:
                children = children[piece].children
            else:
                return i > 0 and not children
        return True

    def debug(self, children=None, indent=""):
        if children is None:
            children = self.children
        for name in sorted(children):
            print("%s%s" % (indent, name))
            self.debug(children[name].children, indent + "\t")
