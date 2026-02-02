"""
Go to page dialog for pagination navigation.
"""

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)


class GoToPageDialog(QDialog):
    """
    Dialog for navigating to a specific page number.
    """

    def __init__(self, current_page: int, total_pages: int, parent=None):
        """
        Initialize the dialog.

        Args:
            current_page: Current page number (1-based for display)
            total_pages: Total number of pages
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Go to Page")
        self.setModal(True)
        self.setMinimumWidth(250)

        self._total_pages = total_pages

        layout = QVBoxLayout(self)

        # Page input row
        input_layout = QHBoxLayout()

        input_layout.addWidget(QLabel("Go to page:"))

        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(max(1, total_pages))
        self.page_spin.setValue(current_page)
        self.page_spin.selectAll()
        input_layout.addWidget(self.page_spin)

        input_layout.addWidget(QLabel(f"/ {total_pages}"))
        input_layout.addStretch()

        layout.addLayout(input_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Focus on spin box
        self.page_spin.setFocus()

    def get_page(self) -> int:
        """
        Get the selected page number (0-based for internal use).

        Returns:
            Page number (0-based)
        """
        return self.page_spin.value() - 1

    @staticmethod
    def get_page_number(
        current_page: int, total_pages: int, parent=None
    ) -> int | None:
        """
        Static method to show dialog and get page number.

        Args:
            current_page: Current page number (1-based for display)
            total_pages: Total number of pages
            parent: Parent widget

        Returns:
            Selected page number (0-based) or None if cancelled
        """
        dialog = GoToPageDialog(current_page, total_pages, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_page()
        return None
