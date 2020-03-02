from typing import Dict
from pysaurus.core.components import AbsolutePath
import os


class PathTreeNode:
    __slots__ = ('name', 'children')

    def __init__(self, name: str):
        self.name = name
        self.children = {}  # type: Dict[str, PathTreeNode]


class PathTree(PathTreeNode):
    __slots__ = ()

    def __init__(self):
        super().__init__('')

    def add(self, path: AbsolutePath):
        pieces = path.standard_path.split(os.sep)
        children = self.children
        for i, piece in enumerate(pieces):
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

    def _debug(self, children, indent):
        for name in sorted(children):
            print('%s%s' % (indent, name))
            self._debug(children[name].children, indent + '\t')

    def debug(self):
        self._debug(self.children, '')
