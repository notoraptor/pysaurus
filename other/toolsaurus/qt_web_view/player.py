import platform
from collections import deque
from typing import Callable, Optional

try:
    import vlc
except BaseException as exc:
    raise RuntimeError("Cannot find or import VLC") from exc

from PyQt5 import QtWidgets, QtCore, QtGui

from pysaurus.core.classes import ToDict
from pysaurus.core.components import ShortDuration as Duration
from pysaurus.core.functions import function_none
from pysaurus.interface.qtwebview.jump_slider import JumpSlider
from saurus.language import say


class MyEvent(ToDict):
    __slots__ = ()

    def handle(self, player):
        pass


class Paused(MyEvent):
    __slots__ = ("__pos",)

    def __init__(self, per_mil: int = None):
        self.__pos = per_mil

    def _get_per_mil(self, player):
        return self.__pos if self.__pos is not None else player._get_pos_per_mil()

    def handle(self, player):
        player.update_paused(self._get_per_mil(player))


class Resumed(Paused):
    __slots__ = ()

    def handle(self, player):
        player.update_resumed(self._get_per_mil(player))


class Moved(Paused):
    __slots__ = ()

    def handle(self, player):
        player.update_moved(self._get_per_mil(player))


class Stopped(MyEvent):
    __slots__ = ("force",)

    def __init__(self, force: bool):
        self.force = force

    def handle(self, player):
        player.update_stopped(self.force)


class Player(QtWidgets.QMainWindow):
    """A simple Media Player using VLC and Qt"""

    on_next: Callable[[], Optional[str]]
    event_manager: vlc.EventManager

    def _mp_media_changed(self, event):
        print("> new media (useless)")

    def _mp_opening(self, event):
        print("> opening")
        self.events.append(Paused(0))

    def _mp_playing(self, event):
        print("> playing")
        self.events.append(Resumed())

    def _mp_paused(self, event):
        print("> paused")
        self.events.append(Paused())

    def _mp_position_changed(self, event):
        print("> new position")
        self.events.append(Moved())

    def _mp_end_reached(self, event):
        print("> end")
        self.end_reached = True

    def _mp_stopped(self, event):
        print("> stopped")
        if self.__is_closing:
            self.__is_closing = False
        else:
            if self.end_reached:
                self.end_reached = False
                self.events.append(Stopped(False))
            else:
                self.events.append(Stopped(True))

    def update_paused(self, per_mil):
        self.play_button.setText(say("\u25B6"))
        self.play_button.setToolTip(say("Play"))
        self.set_slider_display(per_mil)
        self.set_duration_display(per_mil)

    def update_resumed(self, per_mil):
        self.play_button.setText(say("\u23F8"))
        self.play_button.setToolTip(say("Pause"))
        self.set_slider_display(per_mil)
        self.set_duration_display(per_mil)

    def update_moved(self, per_mil):
        self.set_slider_display(per_mil)
        self.set_duration_display(per_mil)

    def update_stopped(self, force):
        if not force and self.repeats():
            self.open_next(True)
        else:
            self.open_next()

    def __init__(self, master=None, *, on_next=None):
        super().__init__(master)
        self.on_next = on_next if callable(on_next) else function_none
        self.play_list = []
        self.events = deque()
        # Flag to prevent recursive call in show event.
        self.__is_showing = False
        self.__is_closing = False
        # Flag to check if player is launched for the first time.
        self.__launched = False
        self.end_reached = False

        # Create a basic vlc instance
        self.instance = vlc.Instance()
        # Create an empty vlc media player
        self.media_player = self.instance.media_player_new()
        # Attach events.
        self.event_manager = self.media_player.event_manager()
        for event_type, callback in (
            (vlc.EventType.MediaPlayerPlaying, self._mp_playing),
            (vlc.EventType.MediaPlayerPaused, self._mp_paused),
            (vlc.EventType.MediaPlayerEndReached, self._mp_end_reached),
            (vlc.EventType.MediaPlayerMediaChanged, self._mp_media_changed),
            (vlc.EventType.MediaPlayerOpening, self._mp_opening),
            (vlc.EventType.MediaPlayerPositionChanged, self._mp_position_changed),
            (vlc.EventType.MediaPlayerStopped, self._mp_stopped),
        ):
            assert self.event_manager.event_attach(event_type, callback) == 0
        # Placeholders
        self.media = None
        self.duration = None

        # UI.

        self.setWindowTitle(say("Media Player"))
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.resize(800, 600)

        if platform.system() == "Darwin":  # for MacOS
            self.video_frame = QtWidgets.QMacCocoaViewContainer(0)
        else:
            self.video_frame = QtWidgets.QFrame()

        self.palette = self.video_frame.palette()
        self.palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        self.video_frame.setPalette(self.palette)
        self.video_frame.setAutoFillBackground(True)

        self.position_slider = JumpSlider(self)
        self.position_slider.setToolTip(say("Position"))
        self.position_slider.setMaximum(1000)
        self.position_slider.valueChanged.connect(self.set_position)

        self.play_button = QtWidgets.QPushButton(say("\u25B6"))
        self.play_button.setToolTip(say("Play"))
        self.play_button.clicked.connect(self.play_pause)

        self.next_button = QtWidgets.QPushButton(say("Next"))
        self.next_button.clicked.connect(self.next)

        self.repeat_button = QtWidgets.QCheckBox(say("Repeat"), self)
        self.repeat_button.setStyleSheet("font-weight: bold;")

        self.duration_label = QtWidgets.QLabel(self)

        self.volume_slider = JumpSlider(self)
        self.volume_slider.setToolTip(say("Volume"))
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(self.media_player.audio_get_volume())
        self.volume_slider.valueChanged.connect(self.set_volume)

        self.h_button_box = QtWidgets.QHBoxLayout()
        self.h_button_box.addWidget(self.play_button)
        self.h_button_box.addWidget(self.next_button)
        self.h_button_box.addWidget(self.repeat_button)
        self.h_button_box.addWidget(self.duration_label)
        self.h_button_box.addStretch(1)
        self.h_button_box.addWidget(self.volume_slider)

        self.vbox_layout = QtWidgets.QVBoxLayout()
        self.vbox_layout.addWidget(self.video_frame)
        self.vbox_layout.addWidget(self.position_slider)
        self.vbox_layout.addLayout(self.h_button_box)

        self.widget = QtWidgets.QWidget(self)
        self.widget.setLayout(self.vbox_layout)
        self.setCentralWidget(self.widget)

        # Shortcuts.

        self.shortcut_play = QtWidgets.QShortcut(QtGui.QKeySequence("Space"), self)
        self.shortcut_play.activated.connect(self.play_pause)

        self.shortcut_next = QtWidgets.QShortcut(QtGui.QKeySequence("N"), self)
        self.shortcut_next.activated.connect(self.next)

        # Timer.

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)

    def update_ui(self):
        if self.events:
            event = self.events.popleft()
            event.handle(self)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        if self.__is_showing:
            return
        self.__is_showing = True
        super().showEvent(event)
        self.timer.start()
        if not self.__launched:
            self.__launched = True
            print("Launch.")
            self.open_next()
        self.__is_showing = False

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.__is_closing = True
        self.__launched = False
        self.timer.stop()
        self.media_player.stop()
        self.events.clear()
        super().closeEvent(event)
        print("Player closed.")

    def set_volume(self, volume):
        """Set the volume"""
        self.media_player.audio_set_volume(volume)

    def set_position(self, pos):
        """Set the movie position according to the position slider."""

        # The vlc MediaPlayer needs a float value between 0 and 1, Qt uses
        # integer variables, so you need a factor; the higher the factor, the
        # more precise are the results (1000 should suffice).

        self.media_player.set_position(pos / 1000.0)

    def next(self):
        self.media_player.stop()

    def open_next(self, reopen=False):
        if reopen:
            assert self.play_list
            path = self.play_list[-1]
            print("Reopening", path)
        else:
            path = self.on_next()
            if not path:
                return
            self.play_list.append(path)
            print("Opening", path)
            if self.media is not None:
                self.media.release()
                self.media = None
            self.media = self.instance.media_new(path)

        # Put the media in the media player
        self.media_player.set_media(self.media)
        self._connect_media_player_to_frame()
        self.media_player.audio_set_volume(self.volume_slider.value())

        # Parse the metadata of the file
        self.media.parse()

        self.duration = Duration(self.media.get_duration() * 1000)
        self.duration_label.setText(str(self.duration))

        # Set the title of the track as window title
        self.setWindowTitle(self.media.get_meta(0))

        self.play_pause()

    def _connect_media_player_to_frame(self):
        # The media player has to be 'connected' to the QFrame (otherwise the
        # video would be displayed in it's own window). This is platform
        # specific, so we must give the ID of the QFrame (or similar object) to
        # vlc. Different platforms have different functions for this
        if platform.system() == "Linux":  # for Linux using the X Server
            self.media_player.set_xwindow(int(self.video_frame.winId()))
        elif platform.system() == "Windows":  # for Windows
            self.media_player.set_hwnd(int(self.video_frame.winId()))
        elif platform.system() == "Darwin":  # for MacOS
            self.media_player.set_nsobject(int(self.video_frame.winId()))
        print("Media player connected.")

    def play_pause(self):
        """Toggle play/pause status"""
        if self.media_player.is_playing():
            self.media_player.pause()
        elif self.media_player.play() != -1:
            self.media_player.play()
        else:
            # TODO
            print("Error playing.")

    def repeats(self):
        return self.repeat_button.checkState() == QtCore.Qt.CheckState.Checked

    def _get_pos_per_mil(self):
        return max(0, int(self.media_player.get_position() * 1000))

    def set_slider_display(self, per_mil):
        old_state = self.position_slider.blockSignals(True)
        self.position_slider.setValue(per_mil)
        self.position_slider.blockSignals(old_state)

    def set_duration_display(self, per_mil):
        current_time = self.duration.total_microseconds * per_mil / 1000
        self.duration_label.setText(f"{Duration(current_time)} / {self.duration}")
