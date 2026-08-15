"""
Modal window hosting a ProcessPage for a single operation.
"""

from typing import Callable

from PySide6.QtWidgets import QDialog, QVBoxLayout

from pysaurus.core.notifications import End
from pysaurus.interface.kyuti.pages.process_page import ProcessPage


class ProcessDialog(QDialog):
    """
    Application-modal dialog displaying the progress of an operation.

    Wraps a ProcessPage: the underlying page stays visible but inert until
    the user clicks Continue, which notifies the caller (the caller then
    hides and destroys this dialog).
    """

    def __init__(
        self, title: str, callback: Callable[[End], None] | None = None, parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(800, 600)

        self.page = ProcessPage(title, callback=callback)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.page)

    def reject(self):
        # Escape key: Continue is the only exit, and it is disabled (so the
        # click is a no-op) while the operation is still running.
        self.page.btn_continue.click()

    def closeEvent(self, event):
        # Same for the window close button: never close on our own, let the
        # Continue path do it.
        event.ignore()
        self.page.btn_continue.click()
