from typing import List, Iterable, Tuple, Union


class VideoSorting:
    __slots__ = "fields", "reverse"
    fields: List[str]
    reverse: List[bool]

    def __init__(self, *raw: Union[str, List[str]]):
        self.fields = []
        self.reverse = []
        for definition in self._to_string_list(*raw):
            for piece in definition.split():
                if piece[0] in "-+":
                    field = piece[1:]
                    descending = piece[0] == "-"
                else:
                    field = piece
                    descending = False
                self.fields.append(field)
                self.reverse.append(descending)

    def __iter__(self) -> Iterable[Tuple[str, bool]]:
        return iter(zip(self.fields, self.reverse))

    @classmethod
    def _to_string_list(cls, *args: Union[str, Iterable[str]]) -> Iterable[str]:
        for arg in args:
            if isinstance(arg, str):
                yield arg
            else:
                for string in arg:
                    yield string
