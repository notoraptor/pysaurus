from typing import List, Tuple

import pygame.freetype
from pygame.freetype import Font as PFFont

from videre import TextAlign

# c, font, x, bounds
CharTaskType = Tuple[str, PFFont, int, pygame.Rect]


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
        _, _, x, bounds = self.tasks[-1]
        return x + bounds.x + bounds.width


class WordTask:
    __slots__ = ("w", "x", "tasks")

    def __init__(self, w: int, x: int, tasks: List[CharTaskType]):
        self.w, self.x, self.tasks = w, x, tasks

    def __repr__(self):
        return f"{self.x}:" + repr("".join(t[0] for t in self.tasks))


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
        return word.x + word.w

    @classmethod
    def from_chars_line(cls, chars_line: CharsLine):
        words = []
        word = []
        for task in chars_line.tasks:
            if task[0] == " ":
                if word:
                    words.append(word)
                    word = []
            else:
                word.append(task)
        if word:
            words.append(word)
        words_line = cls(chars_line.y)
        if words:
            x0 = words[0][0][-2]
            for word in words:
                w_x = word[0][-2]
                x = w_x - x0
                tasks = [(c, font, cx - w_x, bounds) for c, font, cx, bounds in word]
                _, _, last_x, last_bounds = tasks[-1]
                w = last_x + last_bounds.x + last_bounds.width
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
                remaining = width - sum(wt.w for wt in line.words)
                if remaining:
                    interval = remaining / (len(line.words) - 1)
                    x = line.words[0].w + interval
                    for j in range(1, len(line.words)):
                        wt = line.words[j]
                        wt.x = x
                        x += wt.w + interval
