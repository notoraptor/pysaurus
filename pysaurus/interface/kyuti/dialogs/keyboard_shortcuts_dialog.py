"""Dialog listing every keyboard shortcut, built from the actions themselves."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from pysaurus.core.language import say

ShortcutGroups = list[tuple[str, list[QAction]]]


def action_label(action: QAction) -> str:
    """The menu text of an action, without its mnemonic marker."""
    return action.text().replace("&", "")


def shortcut_text(action: QAction) -> str:
    """The key of an action as the platform spells it (Ctrl+O, Del, Esc...)."""
    return action.shortcut().toString(QKeySequence.SequenceFormat.NativeText)


class KeyboardShortcutsDialog(QDialog):
    """Read-only tree of shortcuts: one top-level row per group."""

    def __init__(self, groups: ShortcutGroups, parent=None):
        super().__init__(parent)
        self.setWindowTitle(say("Keyboard Shortcuts"))
        self.resize(560, 620)

        layout = QVBoxLayout(self)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels([say("Action"), say("Shortcut")])
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tree.setRootIsDecorated(False)
        bold = QFont()
        bold.setBold(True)
        for title, actions in groups:
            group_item = QTreeWidgetItem([title, ""])
            group_item.setFont(0, bold)
            group_item.setFirstColumnSpanned(True)
            self.tree.addTopLevelItem(group_item)
            for action in actions:
                group_item.addChild(
                    QTreeWidgetItem([action_label(action), shortcut_text(action)])
                )
        self.tree.expandAll()
        # Labels get the width they need (French ones run long); the key
        # column takes the rest.
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        layout.addWidget(self.tree)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
