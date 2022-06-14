from pysaurus.core.classes import StringPrinter


def dff_dumps(dictionary: dict) -> str:
    with StringPrinter() as writer:
        for key, value in dictionary.items():
            if not isinstance(value, str):
                value = str(value)
            value = value.replace("\r\n", "\n")
            value = value.replace("\r", "\n")
            writer.write(key)
            for line in value.split("\n"):
                writer.write(f"\t{line}")
        return str(writer)


def dff_loads(text: str) -> dict:
    dictionary = {}
    key = None
    lines = []
    for line in text.split("\n"):
        if line.startswith("\t"):
            # value line
            lines.append(line[1:])
        elif not line.strip():
            if key is not None:
                lines.append("")
        else:
            # key
            if key is None:
                assert not lines
            else:
                dictionary[key] = "\n".join(lines)
                lines.clear()
            key = line.strip()
    if key is None:
        assert not lines
    else:
        dictionary[key] = "\n".join(lines)
    return {key: value.rstrip() for key, value in dictionary.items()}


def dff_dump(dictionary: dict, path):
    with open(str(path), "wb") as file:
        file.write(dff_dumps(dictionary).encode("utf-8"))


def dff_load(path) -> dict:
    with open(str(path), "rb") as file:
        return dff_loads(file.read().decode("utf-8"))
