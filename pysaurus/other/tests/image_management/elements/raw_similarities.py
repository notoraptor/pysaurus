from typing import List

import ujson as json

from pysaurus.core.components import AbsolutePath
from pysaurus.core.functions import compute_nb_couples


class RawSimilarities:
    def __init__(self, group_to_paths: List[List[str]]):
        self.group_to_paths = group_to_paths
        self.path_to_group = {
            p: i for i, ps in enumerate(self.group_to_paths) for p in ps
        }

    def __bool__(self):
        return bool(self.group_to_paths)

    def count_couples(self):
        return sum(compute_nb_couples(len(group)) for group in self.group_to_paths)

    def are_connected(self, path, *paths):
        return (g := self.path_to_group.get(path, -1)) != -1 and all(
            g == self.path_to_group.get(p, -1) for p in paths
        )

    def couple_is_connected(self, p1, p2):
        return self.path_to_group.get(p1, -1) == self.path_to_group.get(p2, -1) != -1

    def get_groups(self, paths):
        group_to_paths = {}
        for p in paths:
            group_to_paths.setdefault(self.path_to_group.get(p, -1), []).append(p)
        return [
            sub_paths
            for group_id, sub_paths in group_to_paths.items()
            if group_id > -1 and len(sub_paths) > 1
        ]

    @classmethod
    def new(cls, path=None):
        path = AbsolutePath.ensure(
            path or r"C:\data\git\.local\.html\similarities.json"
        )
        if path.isfile():
            with open(path.path) as file:
                return cls(json.load(file))
        return None
