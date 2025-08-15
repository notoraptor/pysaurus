from pysaurus.core.stringsplit import get_next_word_position


class Pipeline:
    __slots__ = (
        "_in_text",
        "_in_pos",
        "_in_selection",
        "_cursor_is_select_start",
        "out_pos",
        "_out_selection",
        "out_procedure",
    )

    def __init__(self, *, in_text: str, in_pos: int, selection: tuple[int, int] | None):
        self._in_text = in_text
        self._in_pos = in_pos
        self._in_selection = selection

        self._cursor_is_select_start = False
        self.out_pos = None
        self._out_selection = None
        self.out_procedure = []

    def __repr__(self):
        return (
            f"Pipeline(in_text={self._in_text!r}, in_pos={self._in_pos}, "
            f"in_selection={self._in_selection}, "
            f"cursor_is_select_start={self._cursor_is_select_start}, "
            f"out_pos={self.out_pos}, "
            f"out_selection={self.out_selection}, "
            f"out_procedure={[f.__name__ for f in self.out_procedure]})"
        )

    @property
    def out_selection(self) -> tuple[int | None, int | None]:
        return self._out_selection or (None, None)

    def select_no(self):
        assert not self._in_selection
        self._out_selection = None

    def select_out(self):
        self._out_selection = None

    def select_start(self):
        self._out_selection = (self._in_pos, self._in_pos)

    def select_has(self):
        assert self._in_selection
        self._out_selection = self._in_selection

    def ignore_select(self):
        pass

    def find_cursor_in_select(self):
        assert self._out_selection, f"No selection to find cursor in: {self}"
        assert self._in_pos in self._out_selection
        self._cursor_is_select_start = self._in_pos == self._out_selection[0]

    def move_to_next_char(self):
        self.out_pos = min(self._in_pos + 1, len(self._in_text))

    def move_to_next_word(self):
        self.out_pos = get_next_word_position(self._in_text, self._in_pos)

    def move_to_select_end(self):
        selection = self._out_selection or self._in_selection
        assert selection, f"No selection to move cursor to end: {self}"
        if selection[0] == selection[1]:
            # We are getting out of an actually empty selection
            # Let's move to next character
            self.move_to_next_char()
        else:
            # Selection is not empty
            # Let's get out of selection
            # and move just to end of selection
            self.out_pos = selection[1]

    def update_select(self):
        assert self._out_selection is not None
        assert self.out_pos is not None
        if self._cursor_is_select_start:
            self._out_selection = (self.out_pos, self._out_selection[1])
        else:
            self._out_selection = (self._out_selection[0], self.out_pos)


def compute_key_right(
    text: str,
    cursor: int,
    selection: tuple[int, int] | None,
    ctrl: bool | int,
    shift: bool | int,
) -> Pipeline:
    pp = Pipeline(in_text=text, in_pos=cursor, selection=selection)
    proc_1_get_select = None
    proc_2_set_select = None
    proc_3_move_cursor = None
    proc_4_update_select = None

    if shift:
        if selection:
            proc_1_get_select = pp.select_has
        else:
            proc_1_get_select = pp.select_start
        proc_2_set_select = pp.find_cursor_in_select
        proc_4_update_select = pp.update_select
    else:
        if selection:
            proc_1_get_select = pp.select_out
        else:
            proc_1_get_select = pp.select_no
        proc_2_set_select = pp.ignore_select
        proc_4_update_select = pp.ignore_select

    if ctrl:
        proc_3_move_cursor = pp.move_to_next_word
    elif selection and not shift:
        proc_3_move_cursor = pp.move_to_select_end
    else:
        proc_3_move_cursor = pp.move_to_next_char

    pp.out_procedure = [
        proc_1_get_select,
        proc_2_set_select,
        proc_3_move_cursor,
        proc_4_update_select,
    ]
    print(pp)
    for proc in pp.out_procedure:
        proc()

    assert pp.out_pos is not None
    return pp
