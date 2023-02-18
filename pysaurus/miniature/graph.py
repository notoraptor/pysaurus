from typing import Any, Dict, List, Set


class Graph:
    __slots__ = ("edges",)

    def __init__(self):
        self.edges = {}  # type: Dict[Any, List[Any]]

    def connect(self, a, b):
        self.edges.setdefault(a, []).append(b)
        self.edges.setdefault(b, []).append(a)

    def pop_groups(self) -> List[Set[Any]]:
        groups = []
        while self.edges:
            index, other_indices = self.edges.popitem()
            group = {index}
            while other_indices:
                other_index = other_indices.pop()
                if other_index not in group:
                    group.add(other_index)
                    other_indices.extend(self.edges.pop(other_index))
            groups.append(group)
        return groups

    # Unused
    def __remove(self, a):
        for b in self.edges.pop(a):
            self.edges[b].remove(a)
            if not self.edges[b]:
                del self.edges[b]
