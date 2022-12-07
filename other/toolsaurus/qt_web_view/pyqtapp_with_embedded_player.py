import sys

from PyQt5.QtCore import pyqtSignal

from pysaurus.core.notifications import Notification
from pysaurus.interface.qtwebview.run import Api, Interface, PysaurusQtApplication

try:
    from other.toolsaurus.qt_web_view.player import Player

    has_vlc = True
except RuntimeError as exc:
    print("Unable to import VLC player", file=sys.stderr)
    print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
    has_vlc = False


class NextRandomVideo(Notification):
    __slots__ = ()


class ApiWithEmbeddedPlayer(Api):
    __slots__ = ()
    PYTHON_HAS_EMBEDDED_PLAYER = has_vlc

    # Abandoned
    def open_random_player(self):
        self.interface.player_triggered.emit()


class InterfaceWithEmbeddedPlayer(Interface):
    __api_cls__ = ApiWithEmbeddedPlayer
    # Slot set in Python code below
    player_triggered = pyqtSignal()


class PysaurusQtApplicationWithEmbeddedPlayer(PysaurusQtApplication):
    __interface_cls__ = InterfaceWithEmbeddedPlayer

    def __init__(self, *, geometry=None):
        super().__init__(geometry=geometry)
        # setup player
        self.player = None
        if has_vlc:
            self.player = Player(on_next=self._on_next_random_video)
            self.interface.player_triggered.connect(self.player.show)
            if geometry:
                _, _, width, height = geometry
                self.player.resize(int(width * 3 / 4), int(height * 3 / 4))

    def _on_next_random_video(self):
        video_path = self.interface.api.database.provider.choose_random_video(
            open_video=False
        )
        self.interface.api._notify(NextRandomVideo())
        return video_path
