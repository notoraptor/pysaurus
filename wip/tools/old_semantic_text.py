from pysaurus.core.semantic_text import DigitAccumulator, CharClass


def split_numbers_and_texts(text: str) -> list[str | int]:
    output: list[str | int] = []
    accumulator = DigitAccumulator()
    seq = ""
    for character in text:
        wrapper = CharClass(character)
        number = accumulator.append(wrapper)
        if number is not None:
            output.append(number)
        if wrapper.is_alpha():
            seq += character
        elif seq:
            output.append(seq)
            seq = ""
    number = accumulator.append(None)
    if number is not None:
        output.append(number)
    elif seq:
        output.append(seq)
    return output
