from typing import Iterable

from pysaurus.core.components import AbsolutePath
from pysaurus.core.datestring import Date
from pysaurus.core.functions import generate_temporary_file
from pysaurus.core.modules import FileSystem


def create_xspf_playlist(paths: Iterable[AbsolutePath], output=None) -> AbsolutePath:
    tracks = "".join(
        f"<track><location>{filename.uri}</location></track>" for filename in paths
    )
    file_content = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<playlist version="1" xmlns="http://xspf.org/ns/0/">'
        f"<trackList>{tracks}</trackList>"
        f"</playlist>"
    )
    if output is None:
        output = generate_temporary_file(basename="playlist", suffix=".xspf")
    with open(output, "w") as file:
        file.write(file_content)
    return AbsolutePath(output)


def collect_file_titles(folder: AbsolutePath, extension: str) -> dict[str, Date]:
    extension = extension.lower()
    return {
        entry.name[: -(len(extension) + 1)]: Date(entry.stat().st_mtime)
        for entry in FileSystem.scandir(folder.path)
        if entry.path.lower().endswith(f".{extension}")
    }
