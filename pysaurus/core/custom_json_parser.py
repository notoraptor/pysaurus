from typing import Iterator

import ujson as json

EMPTY_CHARACTERS = b" \t\v\r\n"
ARRAY_START = ord("[")
ARRAY_END = ord("]")
OBJECT_START = ord("{")
OBJECT_END = ord("}")
QUOTE = ord('"')
COMMA = ord(",")
ESCAPE = ord("\\")
COLON = ord(":")

OBJ_STEP_KEY = 0
OBJ_STEP_VAL = 1


def _start_sequence(sequence: bytes):
    parsed = None
    iterable = iter(sequence)
    while parsed is None:
        try:
            byte = next(iterable)
        except StopIteration:
            break
        if byte in EMPTY_CHARACTERS:
            continue
        if byte == ARRAY_START:
            parsed = _start_array(iterable)
        elif byte == OBJECT_START:
            parsed = _start_object(iterable)
        else:
            raise ValueError(f"Unexpected byte at JSON start: {byte}")
    if parsed is None:
        raise ValueError("No object or array found in JSON.")
    while True:
        try:
            byte = next(iterable)
        except StopIteration:
            break
        if byte in EMPTY_CHARACTERS:
            continue
        raise ValueError(f"Unexpected byte at JSON end: {byte}")
    return parsed


def _start_array(iterable: Iterator[int]):
    parsed = []
    acc = bytearray()
    nb_commas = 0
    while True:
        try:
            byte = next(iterable)
        except StopIteration:
            raise ValueError("List parsing not finished.")
        if byte in EMPTY_CHARACTERS:
            continue
        if byte == QUOTE:
            parsed.extend(_flush_acc(acc))
            parsed.append(_start_string(iterable))
        elif byte == OBJECT_START:
            parsed.extend(_flush_acc(acc))
            parsed.append(_start_object(iterable))
        elif byte == ARRAY_START:
            parsed.extend(_flush_acc(acc))
            parsed.append(_start_array(iterable))
        elif byte == ARRAY_END:
            parsed.extend(_flush_acc(acc))
            if len(parsed) != nb_commas + 1:
                raise ValueError(
                    f"List: final comma count ({nb_commas}) "
                    f"is not parsed count - 1 ({len(parsed)})"
                )
            break
        elif byte == COMMA:
            parsed.extend(_flush_acc(acc))
            nb_commas += 1
            if len(parsed) != nb_commas:
                raise ValueError(
                    f"List: commas count ({nb_commas}) "
                    f"does not match parsed count ({len(parsed)})"
                )
        else:
            acc.append(byte)
    return parsed


def _start_object(iterable: Iterator[int]):
    parsed = {}
    key = None
    val = bytearray()
    step = OBJ_STEP_KEY
    nb_commas = 0
    while True:
        try:
            byte = next(iterable)
        except StopIteration:
            raise ValueError("Object parsing not finished.")
        if byte in EMPTY_CHARACTERS:
            continue
        if byte == COLON:
            if step != OBJ_STEP_KEY:
                raise ValueError("Colon not following a key.")
            step = OBJ_STEP_VAL
        elif byte == COMMA:
            if step != OBJ_STEP_VAL:
                raise ValueError("Comma not following a value.")
            if val:
                (value,) = _flush_acc(val)
                assert key is not None
                assert key not in parsed
                parsed[key] = value
            nb_commas += 1
            if nb_commas != len(parsed):
                raise ValueError(
                    f"Object: comma count ({nb_commas}) "
                    f"does not match parsed count({len(parsed)})"
                )
            step = OBJ_STEP_KEY
        elif byte == QUOTE:
            element = _start_string(iterable)
            if step == OBJ_STEP_KEY:
                key = element
            else:
                assert key is not None
                assert key not in parsed
                parsed[key] = element
        elif byte == ARRAY_START:
            if step == OBJ_STEP_KEY:
                raise ValueError("Object: array not allowed as key.")
            assert key is not None
            assert key not in parsed
            parsed[key] = _start_array(iterable)
        elif byte == OBJECT_START:
            if step == OBJ_STEP_KEY:
                raise ValueError("Object: object not allowed as key.")
            assert key is not None
            assert key not in parsed
            parsed[key] = _start_object(iterable)
        elif byte == OBJECT_END:
            if step != OBJ_STEP_VAL:
                raise ValueError("Value not preceding object end.")
            if val:
                (value,) = _flush_acc(val)
                assert key is not None
                assert key not in parsed
                parsed[key] = value
            if len(parsed) != nb_commas + 1:
                raise ValueError(
                    f"Object: final comma count ({nb_commas}) "
                    f"is not parsed count - 1 ({len(parsed)})"
                )
            break
        else:
            if step == OBJ_STEP_KEY:
                raise ValueError("Object: non-string not allowed as key.")
            val.append(byte)
    return parsed


def _start_string(iterable: Iterator[int]):
    acc = bytearray()
    while True:
        try:
            byte = next(iterable)
        except StopIteration:
            raise ValueError("String parsing not finished.")
        if byte == QUOTE:
            if acc and acc[-1] == ESCAPE:
                acc.append(byte)
            else:
                break
        else:
            acc.append(byte)
    # ... This ia why I rewrite a JSON parser ...
    # ... To control how strings are decoded ...
    try:
        return acc.decode("utf-8")
    except UnicodeDecodeError:
        return acc.decode("latin-1")


def _flush_acc(acc: bytearray):
    values = []
    if acc:
        string = acc.decode()
        if string == "true":
            values.append(True)
        elif string == "false":
            values.append(False)
        elif string == "null":
            values.append(None)
        else:
            try:
                values.append(int(string))
            except ValueError:
                values.append(float(string))
    acc.clear()
    return values


def custom_json_parse_string(text: str):
    return _start_sequence(text.encode())


def custom_json_parse_file(file):
    return _start_sequence(file.read())


def parse_json(path):
    if not isinstance(path, str):
        path = str(path)
    try:
        with open(path, encoding="utf-8") as file:
            return json.load(file)
    except UnicodeDecodeError:
        print("JSON: falling back to custom parser.")
        with open(path, "rb") as file:
            return custom_json_parse_file(file)
