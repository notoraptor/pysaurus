from typing import Callable

import pyperclip
import videre
from videre.widgets.widget import Widget

from pysaurus.core import notifications
from pysaurus.core.functions import string_to_pieces
from pysaurus.interface.api.api_utils.vlc_path import PYTHON_HAS_RUNTIME_VLC
from pysaurus.interface.using_videre.backend import get_backend
from pysaurus.video.video_pattern import VideoPattern

LIGHT_GREY = videre.parse_color((240, 240, 240))


class DialogRenameVideo(videre.Column):
    __wprops__ = {}
    __slots__ = ("entry",)

    def __init__(self, video: VideoPattern) -> None:
        filename = videre.Text(
            str(video.filename), wrap=videre.TextWrap.CHAR, strong=True
        )
        entry = videre.TextInput(str(video.file_title))
        entry_wrapper = videre.Container(entry, border=videre.Border.all(1))
        self.entry = entry
        super().__init__(
            [filename, entry_wrapper],
            horizontal_alignment=videre.Alignment.CENTER,
            expand_horizontal=True,
            space=10,
        )

    def get_value(self) -> str:
        return self.entry.value


class VideoView(videre.Container):
    __wprops__ = {}
    __slots__ = (
        "_video",
        "_menu",
        "_text_path",
        "_label_title",
        "_hold_file_title",
    )
    __BACKGROUND_EVEN__ = videre.parse_color((240, 240, 240))

    def __init__(self, video: VideoPattern, index: int):
        self._video = video
        checkbox = videre.Checkbox()
        properties = video.properties
        self._menu = videre.ContextButton(
            " \u2630 ",
            actions=self._get_menu_actions(video),
            square=True,
        )
        self._label_title = videre.Label(
            for_button=checkbox, text=str(video.title), strong=True
        )
        self._hold_file_title = videre.Container(
            videre.Text(str(video.file_title)) if video.meta_title else None
        )
        self._text_path = videre.Text(
            str(video.filename),
            wrap=videre.TextWrap.CHAR,
            color=videre.Colors.lightgray if video.watched else videre.Colors.blue,
            strong=video.watched,
        )
        attributes = videre.Column(
            [
                videre.Row(
                    [self._menu, checkbox, self._label_title],
                    vertical_alignment=videre.Alignment.CENTER,
                    space=5,
                ),
                self._hold_file_title,
                self._text_path,
                videre.Text(
                    f"{video.extension.upper()} {video.size} / "
                    f"{video.container_format} /"
                    f" ({video.video_codec}, {video.audio_codec}) / "
                    f"bite rate: {video.bit_rate}/s",
                    wrap=videre.TextWrap.WORD,
                ),
                videre.Text(
                    f"{video.length} | "
                    f"{video.width} x {video.height} @ {round(video.frame_rate)} fps, "
                    f"{video.bit_depth} bits | "
                    f"{video.sample_rate} Hz x {video.audio_bits or '32?'} bits "
                    f"({video.channels} channels), "
                    f"{video.audio_bit_rate_kbps} Kb/s",
                    wrap=videre.TextWrap.WORD,
                ),
                videre.Text(
                    f"{video.date} | "
                    f"(entry) {video.date_entry_modified} | "
                    f"(opened) {video.date_entry_opened}",
                    wrap=videre.TextWrap.WORD,
                ),
                videre.Text(
                    f"Audio: {', '.join(video.audio_languages or ['(none)'])} | "
                    f"Subtitles: {', '.join(video.subtitle_languages or ['(none)'])}"
                ),
                videre.Text(f"Similarity: {video.similarity}"),
            ]
            + (
                [
                    videre.Text("PROPERTIES", strong=True),
                    *(
                        videre.Row(
                            [
                                videre.Text(f"{name}:", strong=True),
                                *(
                                    videre.Container(
                                        videre.Text(str(value), italic=True),
                                        background_color=LIGHT_GREY,
                                        padding=videre.Padding.axis(2, 10),
                                    )
                                    for value in values
                                ),
                            ],
                            space=5,
                            vertical_alignment=videre.Alignment.CENTER,
                        )
                        for name, values in properties.items()
                    ),
                ]
                if properties
                else []
            ),
            space=2,
            weight=1,
        )
        super().__init__(
            videre.Row(
                [
                    videre.Container(
                        videre.Picture(video.thumbnail),
                        width=300,
                        horizontal_alignment=videre.Alignment.CENTER,
                    ),
                    attributes,
                ],
                space=6,
            ),
            padding=videre.Padding.axis(vertical=10),
            background_color=(self.__BACKGROUND_EVEN__ if index % 2 == 1 else None),
        )

    def _get_menu_actions(self, video: VideoPattern) -> list[tuple[str, Callable]]:
        actions = []
        if video.found:
            actions.extend(
                [
                    (
                        f"Mark as {'unwatched' if video.watched else 'watched'}",
                        self._action_change_watched,
                    ),
                    ("Open file", self._action_open_file),
                ]
            )
        if PYTHON_HAS_RUNTIME_VLC:
            actions.extend(
                [("Open from local server", self._action_open_from_local_server)]
            )
        if video.found:
            actions.extend(
                [
                    ("Open containing folder", self._action_open_containing_folder),
                ]
            )
        if video.meta_title:
            actions.extend([("Copy meta title", self._action_copy_meta_title)])
        actions.extend(
            [
                ("Copy file title", self._action_copy_file_title),
                ("Copy path", self._action_copy_path),
                ("Copy video ID", self._action_copy_video_id),
                ("Rename video", self._action_rename),
            ]
        )
        return actions

    def _action_change_watched(self):
        backend = get_backend(self)
        watched = backend.mark_as_read(self._video.video_id)
        video = backend.get_video(self._video.video_id)
        assert video.watched is watched
        self._video = video
        self._text_path.color = (
            videre.Colors.lightgray if video.watched else videre.Colors.blue
        )
        self._text_path.strong = watched
        self._menu.actions = self._get_menu_actions(video)

    def _action_open_file(self):
        get_backend(self).open_video(self._video.video_id)
        self.get_window().notify(notifications.Message("Opened:", self._video.filename))

    def _action_open_from_local_server(self):
        ret = get_backend(self).open_from_server(self._video.video_id)
        self.get_window().notify(notifications.Message("Opened:", ret))

    def _action_open_containing_folder(self):
        ret = get_backend(self).open_containing_folder(self._video.video_id)
        self.get_window().notify(notifications.Message("Opened folder:", ret))

    def _action_copy_meta_title(self):
        self._action_copy("meta_title")

    def _action_copy_file_title(self):
        self._action_copy("file_title")

    def _action_copy_path(self):
        self._action_copy("filename", "path")

    def _action_copy_video_id(self):
        self._action_copy("video_id", "video ID")

    def _action_copy(self, field: str, title=None):
        title = title or " ".join(string_to_pieces(field))
        value = getattr(self._video, field)
        pyperclip.copy(str(value))
        self.get_window().notify(notifications.Message(f"Copied {title}:", value))

    def _action_rename(self):
        dialog = DialogRenameVideo(self._video)
        button = videre.Button("rename", on_click=self._on_rename, data=dialog)
        self.get_window().set_fancybox(dialog, title="Rename Video", buttons=[button])

    def _on_rename(self, widget: Widget):
        dialog: DialogRenameVideo = widget.data
        new_title = dialog.get_value()
        widget.data = None
        backend = get_backend(self)
        backend.rename_video(self._video.video_id, new_title)
        video = backend.get_video(self._video.video_id)
        self._video = video
        self._label_title.text = str(video.title)
        self._text_path.text = str(video.filename)
        self._hold_file_title.control = (
            videre.Text(str(video.file_title)) if video.meta_title else None
        )
        window = self.get_window()
        window.clear_fancybox()
        window.notify(notifications.Message(f"Renamed to: {new_title}:"))
