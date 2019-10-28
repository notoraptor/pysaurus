class LeafError(Exception):
    pass


class RootError(Exception):
    pass


class AbstractNode:
    __slots__ = '__parent', '__children', '__allow_parent', '__allow_children'

    def __init__(self, *, allow_parent=True, allow_children=True):
        self.__parent = None
        self.__children = []
        self.__allow_parent = allow_parent
        self.__allow_children = allow_children

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, parent):
        if not self.__allow_parent:
            raise RootError()
        self.__parent = parent

    def append(self, child):
        # type: (AbstractNode) -> None
        if not self.__allow_children:
            raise LeafError()
        self.__children.append(child)
        child.parent = self

    def extend(self, children):
        if not self.__allow_children:
            raise LeafError()
        for child in children:
            self.__children.append(child)
            child.parent = self

    def clear(self):
        self.__children.clear()

    def remove(self, index):
        self.__children.pop(index)

    def __len__(self):
        return len(self.__children)

    def __getitem__(self, item):
        return self.__children[item]

    def __iter__(self):
        return iter(self.__children)

    def __str__(self):
        if not self.__allow_children:
            return type(self).__name__
        return '%s(%s)' % (type(self).__name__, ','.join(str(child) for child in self.__children))


class Node(AbstractNode):
    __slots__ = ()

    def __init__(self, *children):
        super().__init__()
        self.extend(children)


class Root(AbstractNode):
    __slots__ = ()

    def __init__(self, *children):
        super().__init__(allow_parent=False, allow_children=True)
        self.extend(children)


class Leaf(AbstractNode):
    __slots__ = ()

    def __init__(self):
        super().__init__(allow_parent=True, allow_children=False)


def main():
    print(Root(
        Leaf(),
        Leaf(),
        Leaf(),
        Leaf(),
        Node(
            Leaf(),
            Leaf(),
            Leaf()
        ),
        Node(
            Leaf(),
            Leaf(),
            Node(
                Leaf(),
                Node(),
                Leaf(),
                Node(),
            ),
            Leaf(),
            Leaf(),
        ),
        Leaf(),
        Node()
    ))


if __name__ == '__main__':
    main()
