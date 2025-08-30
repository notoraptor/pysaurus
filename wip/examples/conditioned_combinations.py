import pprint
from collections.abc import Sequence
from dataclasses import dataclass

from strarr import strarr


@dataclass(slots=True)
class Case:
    case: tuple[int, ...]
    sequence: Sequence


class Procedure:
    __slots__ = ("sequence",)

    def __init__(self, sequence: Sequence[str]):
        self.sequence = sequence

    def __repr__(self):
        return ", ".join(self.sequence)


def check(cases: Sequence[Case], criterions: Sequence[str]) -> None:
    assert cases
    assert criterions
    nb_criterions = len(criterions)
    nb_combinaisons = 2**nb_criterions
    nb_per_criteria = nb_combinaisons // 2
    assert len(cases) == nb_combinaisons, (
        f"Expected {nb_combinaisons} cases, got {len(cases)}"
    )

    proc_to_cases: dict[str, list[tuple[int, ...]]] = {}
    proc_to_2_cases: dict[str, dict[tuple, list[tuple[int, ...]]]] = {}
    names_cases = []
    for case in cases:
        assert len(case.case) == nb_criterions, (
            f"Case {case.case} does not match the number of criterions {nb_criterions}"
        )
        named_case = {name: val for (name, val) in zip(criterions, case.case)} | {
            "sequence": Procedure(case.sequence)
        }
        names_cases.append(named_case)

        double_combs = _combine_values(range(nb_criterions), 2)

        for proc in case.sequence:
            special_case = tuple(val or -1 for val in case.case)
            proc_to_cases.setdefault(proc, []).append(special_case)
            for comb in double_combs:
                sub_case = [special_case[i] for i in comb]
                proc_to_2_cases.setdefault(proc, {}).setdefault(comb, []).append(
                    tuple(sub_case)
                )
                if proc == "select_has":
                    print(">>>", proc, comb, sub_case)
                    print(">>>", proc_to_2_cases[proc][comb])

    print(strarr(names_cases, align_left=True, index=None))
    print()
    pprint.pprint(proc_to_cases)
    print()
    for proc, special_cases in proc_to_cases.items():
        sums = _sum_sequences(*special_cases)
        cond = []
        for i, val in enumerate(sums):
            if val:
                if val == nb_per_criteria:
                    cond.append(criterions[i])
                elif val == -nb_per_criteria:
                    cond.append(f"not {criterions[i]}")
        if len(cond) == 1:
            print(f"{proc}:", *cond)
        else:
            print(f"~ {proc}:", sums)
    print()
    for proc, comb_to_cases in proc_to_2_cases.items():
        for comb, special_sub_cases in comb_to_cases.items():
            sums = _sum_sequences(*special_sub_cases)
            cond = []
            for i, val in enumerate(sums):
                if val:
                    if val == nb_per_criteria // 2:
                        cond.append(criterions[comb[i]])
                    elif val == -nb_per_criteria // 2:
                        cond.append(f"not {criterions[comb[i]]}")
            if len(cond) == 2:
                print(f"{proc} {comb}:", cond)
            else:
                print(f"~ {proc} {comb}:", sums, cond)


def _sum_sequences(*sequences: Sequence[int]) -> list[int]:
    assert len(sequences) > 0
    first, *others = sequences
    result = list(first)
    for other in others:
        assert len(other) == len(result)
        for i, val in enumerate(other):
            result[i] += val
    return result


def _combine_values(values: Sequence, nb: int) -> list[tuple[int, ...]]:
    if nb <= 0:
        return [()]
    result = []
    for i, val in enumerate(values):
        for other_comb in _combine_values(values[i + 1 :], nb - 1):
            result.append((val, *other_comb))
    return result


def main_right():
    criterions = ("ctrl", "shift", "select")
    cases = [
        Case(
            (0, 0, 0),
            ["select_no", "ignore_select", "move_to_next_char", "ignore_select_2"],
        ),
        Case(
            (0, 0, 1),
            ["select_out", "ignore_select", "move_to_select_end", "ignore_select_2"],
        ),
        Case(
            (0, 1, 0),
            [
                "select_start",
                "find_cursor_in_select",
                "move_to_next_char",
                "update_select",
            ],
        ),
        Case(
            (0, 1, 1),
            [
                "select_has",
                "find_cursor_in_select",
                "move_to_next_char",
                "update_select",
            ],
        ),
        Case(
            (1, 0, 0),
            ["select_no", "ignore_select", "move_to_next_word", "ignore_select_2"],
        ),
        Case(
            (1, 0, 1),
            ["select_out", "ignore_select", "move_to_next_word", "ignore_select_2"],
        ),
        Case(
            (1, 1, 0),
            [
                "select_start",
                "find_cursor_in_select",
                "move_to_next_word",
                "update_select",
            ],
        ),
        Case(
            (1, 1, 1),
            [
                "select_has",
                "find_cursor_in_select",
                "move_to_next_word",
                "update_select",
            ],
        ),
    ]
    check(cases, criterions)


def main_left():
    criterions = ("ctrl", "shift", "select")
    cases = [
        Case(
            (0, 0, 0),
            ["select_no", "ignore_select", "move_to_previous_char", "ignore_select_2"],
        ),
        Case(
            (0, 0, 1),
            ["select_out", "ignore_select", "move_to_select_start", "ignore_select_2"],
        ),
        Case(
            (0, 1, 0),
            [
                "select_start",
                "find_cursor_in_select",
                "move_to_previous_char",
                "update_select",
            ],
        ),
        Case(
            (0, 1, 1),
            [
                "select_has",
                "find_cursor_in_select",
                "move_to_previous_char",
                "update_select",
            ],
        ),
        Case(
            (1, 0, 0),
            ["select_no", "ignore_select", "move_to_previous_word", "ignore_select_2"],
        ),
        Case(
            (1, 0, 1),
            ["select_out", "ignore_select", "move_to_previous_word", "ignore_select_2"],
        ),
        Case(
            (1, 1, 0),
            [
                "select_start",
                "find_cursor_in_select",
                "move_to_previous_word",
                "update_select",
            ],
        ),
        Case(
            (1, 1, 1),
            [
                "select_has",
                "find_cursor_in_select",
                "move_to_previous_word",
                "update_select",
            ],
        ),
    ]
    check(cases, criterions)


if __name__ == "__main__":
    main_left()
