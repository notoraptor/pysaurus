from typing import Iterable, List, Tuple


class VideoSorting:
    __slots__ = "fields", "reverse"
    fields: List[str]
    reverse: List[bool]

    def __init__(self, sorting: Iterable[str]):
        self.fields = []
        self.reverse = []
        for piece in sorting:
            if piece[0] in "-+":
                field = piece[1:]
                descending = piece[0] == "-"
            else:
                field = piece
                descending = False
            self.fields.append(field)
            self.reverse.append(descending)

    def __len__(self):
        return len(self.fields)

    def __iter__(self) -> Iterable[Tuple[str, bool]]:
        return iter(zip(self.fields, self.reverse))

    def __eq__(self, other):
        return self.fields == other.fields and self.reverse == other.reverse

    def to_string_list(self):
        return [
            f"{'-' if reverse else '+'}{field}"
            for field, reverse in zip(self.fields, self.reverse)
        ]
