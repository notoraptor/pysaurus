from typing import List, Self

from pysaurus.core.unicode_utils import Unicode
from videre import TextAlign


class CharTaskType:
    __slots__ = ("font", "c", "width", "horizontal_shift", "x")

    def __init__(self, c: str, size: int, fonts: "PygameFontFactory"):
        font = fonts.get_font(c)
        bounds = font.get_rect(c, size=size)
        (metric,) = font.get_metrics(c, size=size)

        self.font = font
        self.c = c
        self.width = bounds.x + bounds.width
        self.horizontal_shift = metric[4] if metric else bounds.width
        self.x = 0

    def is_newline(self) -> bool:
        return self.c == "\n"

    def is_printable(self) -> bool:
        return Unicode.printable(self.c)

    def at(self, x: int) -> Self:
        self.x = x
        return self


class CharsLine:
    __slots__ = ("y", "tasks", "newline")
    y: int
    tasks: List[CharTaskType]
    newline: bool

    def __init__(self, newline=False):
        self.y, self.tasks, self.newline = 0, [], newline

    def __bool__(self):
        return bool(self.tasks or self.newline)

    def limit(self) -> int:
        info = self.tasks[-1]
        return info.x + info.width


class WordTask:
    __slots__ = ("x", "width", "tasks")
    x: int
    width: int
    tasks: List[CharTaskType]

    def __init__(self, width: int, x: int, tasks: List[CharTaskType]):
        self.width = width
        self.tasks = tasks
        self.x = x

    def __repr__(self):
        return f"{self.x}:" + repr("".join(t.c for t in self.tasks))


class WordTaskType(WordTask):
    __slots__ = ("height", "horizontal_shift")

    width: int
    height: int
    tasks: List[CharTaskType]

    def __init__(
        self,
        word: str,
        size: int,
        height_delta: int,
        line_spacing: int,
        space_width: int,
        fonts: "PygameFontFactory",
    ):
        width, height, lines = fonts._get_render_tasks(
            word, None, size, height_delta, False, line_spacing
        )
        if width:
            (line,) = lines
            tasks = line.tasks
        else:
            tasks = []
        super().__init__(width, 0, tasks)
        self.horizontal_shift = self.width + space_width
        self.height = height

    def is_newline(self) -> bool:
        return self.height and not self.width

    def is_printable(self) -> bool:
        return bool(self.width)

    def at(self, x: int) -> Self:
        self.x = x
        return self


class WordsLine:
    __slots__ = ("y", "words", "newline")
    y: int
    words: List[WordTask]
    newline: bool

    def __init__(self, y=0, newline=False):
        self.y, self.words, self.newline = y, [], newline

    def __bool__(self):
        return bool(self.words or self.newline)

    def __repr__(self):
        return f"({self.y}, {self.words})"

    def limit(self) -> int:
        word = self.words[-1]
        return word.x + word.width

    @classmethod
    def from_chars_line(cls, chars_line: CharsLine) -> Self:
        words: List[List[CharTaskType]] = []
        word: List[CharTaskType] = []
        for task in chars_line.tasks:
            if task.c == " ":
                if word:
                    words.append(word)
                    word = []
            else:
                word.append(task)
        if word:
            words.append(word)
        words_line = cls(chars_line.y)
        if words:
            x0 = words[0][0].x
            for word in words:
                w_x = word[0].x
                x = w_x - x0
                tasks = [ch.at(ch.x - w_x) for ch in word]
                last_ch = tasks[-1]
                w = last_ch.x + last_ch.width
                words_line.words.append(WordTask(w, x, tasks))
        return words_line


def align_words(lines: List[WordsLine], width: int, align=TextAlign.LEFT):
    if align == TextAlign.NONE or align == TextAlign.LEFT:
        return
    if align == TextAlign.JUSTIFY:
        return justify_words(lines, width)
    for line in lines:
        if line.words:
            assert line.words[0].x == 0, line
            remaining = width - line.limit()
            if remaining:
                if align == TextAlign.CENTER:
                    remaining /= 2
                for wt in line.words:
                    wt.x += remaining


def justify_words(lines: List[WordsLine], width: int):
    paragraphs = []
    p = []
    for line in lines:
        if line.words:
            p.append(line)
        elif p:
            paragraphs.append(p)
            p = []
    if p:
        paragraphs.append(p)

    for paragraph in paragraphs:
        for i in range(len(paragraph) - 1):
            line = paragraph[i]
            if len(line.words) > 1:
                assert line.words[0].x == 0
                remaining = width - sum(wt.width for wt in line.words)
                if remaining:
                    interval = remaining / (len(line.words) - 1)
                    x = line.words[0].width + interval
                    for j in range(1, len(line.words)):
                        wt = line.words[j]
                        wt.x = x
                        x += wt.width + interval
