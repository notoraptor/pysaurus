"""Per-video properties dialog — edit custom properties + read-only metadata.

Shown as fancybox content (OK/Cancel are FancyCloseButtons on the page side).
Two tabs (kyuti VideoPropertiesDialog): **Properties** = one section per
property type with a type-appropriate editor; **Info** = read-only metadata
groups (File/Video/Audio/Status). ``get_changes()`` returns only the properties
whose value differs from what was loaded, as ``{name: [values]}`` (an empty
list deletes the property from the video).

Editor semantics — everything is READ FROM THE WIDGETS, no hidden state, since
videre has no change events (G24 TextInput / G21 Dropdown) to track "modified"
live (kyuti's blue styling, per-prop Reset/Clear buttons and focus-bold are
dropped for the same reason; Cancel is the global reset):

- single str/int/float -> TextInput; **blank = no value** (deletes if the
  property was defined); an unparseable int/float is IGNORED (kyuti skips
  ValueError on accept).
- single enum/bool -> Dropdown with a leading **"(no value)"** sentinel (kyuti
  uses a Clear button instead; a sentinel keeps the state inspectable).
- multiple enum -> one Checkbox per allowed value.
- multiple free -> value list (one ✕ per value) + input + "+" + Clear.
- An UNDEFINED property loads empty/sentinel, not the type default: without
  kyuti's italic "showing default" styling, a pre-filled editor would read as
  a set value.
"""

from __future__ import annotations

import videre
from videre.widgets.widget import Widget

from pysaurus.core.duration import Duration
from pysaurus.core.file_size import FileSize
from pysaurus.interface.videroid import theme
from pysaurus.interface.videroid.widgets.tabs import Tabs

_NO_VALUE = "(no value)"


class VideoPropertiesDialog(videre.Column):
    __wprops__ = {}
    __slots__ = ("_video", "_prop_types", "_editors")

    def __init__(self, video, prop_types):
        self._video = video
        self._prop_types = list(prop_types)
        # name -> editor record: {"kind", "initial": list, widgets...}
        self._editors: dict[str, dict] = {}
        super().__init__(
            [
                Tabs(
                    [("Properties", self._build_properties), ("Info", self._build_info)]
                )
            ],
            space=8,
            expand_horizontal=True,
        )

    # --- properties tab -------------------------------------------------------

    def _build_properties(self) -> Widget:
        if not self._prop_types:
            return videre.Text("No custom properties defined.", italic=True)
        sections = [
            self._section(index, prop) for index, prop in enumerate(self._prop_types)
        ]
        return videre.Container(
            videre.ScrollView(
                videre.Column(sections, space=0, expand_horizontal=True),
                wrap_horizontal=True,
            ),
            height=340,
        )

    def _section(self, index: int, prop) -> Widget:
        details = [prop.type]
        if prop.multiple:
            details.append("multiple")
        if prop.enumeration:
            details.append("enum")
        header = videre.Text(f"{prop.name}  ({', '.join(details)})", strong=True)
        editor = self._make_editor(prop)
        return videre.Container(
            videre.Column([header, editor], space=4, expand_horizontal=True),
            background_color=(theme.SECTION_BG_A if index % 2 else theme.SECTION_BG_B),
            padding=videre.Padding.all(8),
        )

    def _stored(self, prop) -> list:
        """The property's values as stored on the video (empty if undefined)."""
        values = (self._video.properties or {}).get(prop.name) or []
        return [v for v in values if v is not None]

    def _make_editor(self, prop) -> Widget:
        stored = self._stored(prop)
        if prop.multiple and prop.enumeration:
            return self._make_multi_enum(prop, stored)
        if prop.multiple:
            return self._make_multi_list(prop, stored)
        if prop.enumeration or prop.type == "bool":
            return self._make_single_choice(prop, stored)
        return self._make_single_text(prop, stored)

    def _make_single_text(self, prop, stored) -> Widget:
        widget = videre.TextInput(str(stored[0]) if stored else "")
        self._editors[prop.name] = {
            "kind": "single_text",
            "prop": prop,
            "widget": widget,
            "initial": stored[:1],
        }
        return widget

    def _make_single_choice(self, prop, stored) -> Widget:
        # Enum values keep their original type; bool is offered as true/false
        # (mapped back on read, like the batch-edit dialog).
        options = list(prop.enumeration) if prop.enumeration else ["true", "false"]
        current = stored[0] if stored else None
        if prop.type == "bool" and current is not None:
            current = "true" if current else "false"
        choices = [_NO_VALUE, *options]
        widget = videre.Dropdown(choices)
        if current is not None and current in options:
            widget.index = choices.index(current)
        self._editors[prop.name] = {
            "kind": "single_choice",
            "prop": prop,
            "widget": widget,
            "initial": stored[:1],
        }
        return widget

    def _make_multi_enum(self, prop, stored) -> Widget:
        stored_set = set(stored)
        checks = [
            (value, videre.Checkbox(checked=value in stored_set))
            for value in prop.enumeration
        ]
        self._editors[prop.name] = {
            "kind": "multi_enum",
            "prop": prop,
            "checks": checks,
            # Normalized to enumeration order so an untouched editor reads back
            # exactly its initial value.
            "initial": [value for value in prop.enumeration if value in stored_set],
        }
        return videre.Column(
            [
                videre.Row(
                    [box, videre.Label(for_button=box, text=str(value))],
                    space=4,
                    vertical_alignment=videre.Alignment.CENTER,
                )
                for value, box in checks
            ],
            space=2,
        )

    def _make_multi_list(self, prop, stored) -> Widget:
        record = {
            "kind": "multi_list",
            "prop": prop,
            "values": list(stored),
            "input": videre.TextInput(),
            "column": videre.Column([], space=2, expand_horizontal=True),
            "error": videre.Text("", color="#cc0000"),
            "initial": list(stored),
        }
        self._editors[prop.name] = record
        name = prop.name
        self._render_list(name)
        return videre.Column(
            [
                record["column"],
                videre.Row(
                    [
                        record["input"],
                        videre.Button("+", on_click=lambda w: self._add_value(name)),
                        videre.Button(
                            "Clear", on_click=lambda w: self._clear_list(name)
                        ),
                    ],
                    space=4,
                    vertical_alignment=videre.Alignment.CENTER,
                ),
                record["error"],
            ],
            space=4,
            expand_horizontal=True,
        )

    def _render_list(self, name: str) -> None:
        record = self._editors[name]
        rows = [
            videre.Row(
                [
                    videre.Text(str(value), weight=1, wrap=videre.TextWrap.WORD),
                    videre.Button(
                        "✕", on_click=lambda w, v=value: self._remove_value(name, v)
                    ),
                ],
                space=4,
                vertical_alignment=videre.Alignment.CENTER,
            )
            for value in record["values"]
        ]
        record["column"].controls = rows or [videre.Text("(no value)", italic=True)]

    def _parse(self, prop, text: str):
        """Parse `text` for the property's type; None if blank or unparseable."""
        text = text.strip()
        if not text:
            return None
        try:
            if prop.type == "int":
                return int(text)
            if prop.type == "float":
                return float(text)
        except ValueError:
            return None
        return text

    def _add_value(self, name: str) -> None:
        record = self._editors[name]
        text = record["input"].value
        value = self._parse(record["prop"], text)
        if value is None:
            if text.strip():
                record["error"].text = f"Invalid value for type {record['prop'].type}."
            return
        record["error"].text = ""
        if value not in record["values"]:
            record["values"].append(value)
            self._render_list(name)
        record["input"].value = ""

    def _remove_value(self, name: str, value) -> None:
        record = self._editors[name]
        record["values"] = [v for v in record["values"] if v != value]
        self._render_list(name)

    def _clear_list(self, name: str) -> None:
        record = self._editors[name]
        record["values"] = []
        record["error"].text = ""
        self._render_list(name)

    # --- reading --------------------------------------------------------------

    def _read(self, record) -> list:
        """Current editor value as a list; `initial` back if input is invalid."""
        kind = record["kind"]
        if kind == "single_text":
            text = record["widget"].value
            value = self._parse(record["prop"], text)
            if value is None and text.strip():
                return record["initial"]  # unparseable int/float: ignore (kyuti)
            return [] if value is None else [value]
        if kind == "single_choice":
            selected = record["widget"].selected
            if selected == _NO_VALUE:
                return []
            if record["prop"].type == "bool":
                return [selected == "true"]
            return [selected]
        if kind == "multi_enum":
            return [value for value, box in record["checks"] if box.checked]
        return list(record["values"])  # multi_list

    def get_changes(self) -> dict[str, list]:
        """Properties whose value changed: {name: [values]}, [] = delete."""
        changes = {}
        for name, record in self._editors.items():
            new = self._read(record)
            if new != record["initial"]:
                changes[name] = new
        return changes

    # --- info tab ---------------------------------------------------------------

    def _build_info(self) -> Widget:
        video = self._video
        file_rows = [
            ("Title:", video.title),
            ("Filename:", video.filename),
            ("Size:", FileSize(video.file_size)),
            ("Date Modified:", video.date_entry_modified),
        ]
        video_rows = [
            (
                "Duration:",
                Duration(int(video.duration * 1_000_000))
                if video.duration is not None
                else "N/A",
            ),
            ("Resolution:", f"{video.width}x{video.height}"),
            ("Codec:", video.video_codec or "N/A"),
            ("Codec Description:", video.video_codec_description or "N/A"),
            ("Container:", video.container_format or "N/A"),
        ]
        if video.frame_rate_den:
            fps = video.frame_rate_num / video.frame_rate_den
            video_rows.append(("Frame Rate:", f"{fps:.2f} fps"))
        audio_rows = [
            ("Codec:", video.audio_codec or "N/A"),
            ("Channels:", video.channels or "N/A"),
            ("Sample Rate:", f"{video.sample_rate} Hz" if video.sample_rate else "N/A"),
            (
                "Bit Rate:",
                f"{video.audio_bit_rate_formatted}/s"
                if video.audio_bit_rate
                else "N/A",
            ),
        ]
        status_rows = [
            ("Found:", "Yes" if video.found else "No"),
            ("Readable:", "No" if video.unreadable else "Yes"),
            ("Has Thumbnail:", "Yes" if video.with_thumbnails else "No"),
        ]
        if video.similarity_id is not None:
            status_rows.append(("Similarity Group:", video.similarity_id))
        if video.similarity_id_reencoded is not None:
            status_rows.append(("Re-encoded Group:", video.similarity_id_reencoded))
        return videre.Container(
            videre.ScrollView(
                videre.Column(
                    [
                        self._info_group("File", file_rows),
                        self._info_group("Video", video_rows),
                        self._info_group("Audio", audio_rows),
                        self._info_group("Status", status_rows),
                    ],
                    space=8,
                    expand_horizontal=True,
                ),
                wrap_horizontal=True,
            ),
            height=340,
        )

    @staticmethod
    def _info_group(title: str, rows: list[tuple[str, object]]) -> Widget:
        return videre.Container(
            videre.Column(
                [videre.Text(title, strong=True)]
                + [
                    videre.Row(
                        [
                            videre.Text(label, strong=True),
                            videre.Text(
                                str(value), wrap=videre.TextWrap.CHAR, weight=1
                            ),
                        ],
                        space=6,
                    )
                    for label, value in rows
                ],
                space=2,
                expand_horizontal=True,
            ),
            border=videre.Border.all(1, videre.Colors.lightgray),
            padding=videre.Padding.all(6),
        )
