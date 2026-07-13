from typing import Iterable, Iterator


class VideoSorting:
    __slots__ = "fields", "reverse"
    fields: list[str]
    reverse: list[bool]

    def __init__(self, sorting: Iterable[str]):
        self.fields = []
        self.reverse = []
        seen: set[str] = set()
        for piece in sorting:
            if piece[:1] in ("-", "+"):
                field = piece[1:]
                descending = piece[0] == "-"
            else:
                field = piece
                descending = False
            # Sorting a field twice is meaningless: the first occurrence already
            # fully orders it. Keep the first entry per field, drop later dupes.
            if field in seen:
                continue
            seen.add(field)
            self.fields.append(field)
            self.reverse.append(descending)

    def __len__(self):
        return len(self.fields)

    def __iter__(self) -> Iterator[tuple[str, bool]]:
        # NB: We must annotate with Iterator, not Iterable,
        # so that type checkers detect this class as iterable.
        return iter(zip(self.fields, self.reverse))

    def __eq__(self, other):
        return self.fields == other.fields and self.reverse == other.reverse

    def to_string_list(self):
        return [
            f"{'-' if reverse else '+'}{field}"
            for field, reverse in zip(self.fields, self.reverse)
        ]
