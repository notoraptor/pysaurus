from typing import Iterable

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.functions import generate_temporary_file


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
