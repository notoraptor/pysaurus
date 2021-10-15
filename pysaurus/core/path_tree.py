import os
from typing import Dict

from pysaurus.core.classes import StringPrinter
from pysaurus.core.components import AbsolutePath


class PathTreeNode:
    __slots__ = "name", "children", "termination"

    def __init__(self, name: str):
        self.name = name
        self.children = {}  # type: Dict[str, PathTreeNode]
        self.termination = False


class PathTree(PathTreeNode):
    __slots__ = ()

    def __init__(self, folders=()):
        super().__init__("")
        for folder in folders:
            self.add(folder)

    def add(self, path: AbsolutePath):
        current = self
        for piece in path.standard_path.split(os.sep):
            if piece in current.children:
                node = current.children[piece]
            else:
                node = PathTreeNode(piece)
                current.children[node.name] = node
            current = node
        current.termination = True

    def in_folders(self, path: AbsolutePath):
        pieces = path.standard_path.split(os.sep)
        current = self
        for i, piece in enumerate(pieces):
            if piece in current.children:
                current = current.children[piece]
            else:
                break
        return current.name and current.termination

    def __debug(self, output: StringPrinter, children, indent=""):
        for name in sorted(children):
            output.write(indent + name)
            self.__debug(output, children[name].children, indent + "\t")

    def __str__(self):
        printer = StringPrinter()
        self.__debug(printer, self.children)
        return str(printer)
