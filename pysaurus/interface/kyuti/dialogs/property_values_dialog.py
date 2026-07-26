"""
Dialog for managing property values across all videos.
"""

from collections import Counter

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from pysaurus.core.language import say
from pysaurus.interface.kyuti.widgets.left_click_menu import LeftClickMenu
from pysaurus.properties.properties import PROP_UNIT_CONVERTER, PropType, PropUnitType
from pysaurus.properties.property_value_modifier import PropertyValueModifier


class PropertyValuesDialog(QDialog):
    """
    Dialog for viewing and managing all values of a property.

    Features:
    - List all values with their usage count
    - Delete values (removes from all videos)
    - Rename/merge values
    - Apply modifiers (lowercase, uppercase)
    """

    def __init__(self, prop_name: str, prop_type: PropType, ctx, parent=None):
        super().__init__(parent)
        self.prop_name = prop_name
        self.prop_type = prop_type
        self.ctx = ctx
        self._values_count: dict[PropUnitType, int] = {}
        self._modified = False

        self.setWindowTitle(say("Values - {prop_name}", prop_name=prop_name))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        # Header info
        type_name = self.prop_type.type
        multiple = say("Yes") if self.prop_type.multiple else say("No")
        info_label = QLabel(
            say(
                "<b>{prop_name}</b> (type: {type_name}, multiple: {multiple})",
                prop_name=self.prop_name,
                type_name=type_name,
                multiple=multiple,
            )
        )
        layout.addWidget(info_label)

        # Main content: values list and actions
        content_layout = QHBoxLayout()

        # Values list
        list_layout = QVBoxLayout()
        list_layout.addWidget(
            QLabel(say("Values (click to select, right-click for actions):"))
        )

        self.values_list = QListWidget()
        self.values_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.values_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.values_list.customContextMenuRequested.connect(self._on_context_menu)
        list_layout.addWidget(self.values_list)

        content_layout.addLayout(list_layout, 1)

        # Actions panel
        actions_layout = QVBoxLayout()
        actions_layout.addWidget(QLabel(say("Actions:")))

        self.btn_delete = QPushButton(say("Delete Selected"))
        self.btn_delete.setToolTip(say("Remove selected values from all videos"))
        self.btn_delete.clicked.connect(self._on_delete)
        actions_layout.addWidget(self.btn_delete)

        self.btn_rename = QPushButton(say("Rename Value..."))
        self.btn_rename.setToolTip(say("Rename a value (merges if target exists)"))
        self.btn_rename.clicked.connect(self._on_rename)
        actions_layout.addWidget(self.btn_rename)

        # Modifiers are text transforms (lowercase, strip...), so they are only
        # offered for str properties.
        self._modifier_buttons: list[QPushButton] = []
        if self.prop_type.type == "str":
            actions_layout.addSpacing(20)
            actions_layout.addWidget(QLabel(say("Apply to all values:")))

            # Get available modifiers from PropertyValueModifier
            modifiers = PropertyValueModifier.get_modifiers()
            for mod_name in modifiers:
                btn = QPushButton(mod_name.replace("_", " ").title())
                btn.setToolTip(
                    say("Apply '{mod_name}' to all values", mod_name=mod_name)
                )
                btn.setProperty("mod_name", mod_name)
                btn.clicked.connect(self._on_modifier_clicked)
                actions_layout.addWidget(btn)
                self._modifier_buttons.append(btn)

        actions_layout.addStretch()

        # Stats
        self.stats_label = QLabel("")
        actions_layout.addWidget(self.stats_label)

        content_layout.addLayout(actions_layout)
        layout.addLayout(content_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)

    def _load_values(self):
        """Load all values for this property."""
        self.values_list.clear()
        self._values_count.clear()

        if not self.ctx.has_database():
            return

        # Get all values with counts
        all_values = self.ctx.get_property_values(self.prop_name)
        counter = Counter()
        for values in all_values.values():
            counter.update(values)

        self._values_count = dict(counter)

        # Sort by count (descending) then by value
        sorted_values = sorted(
            self._values_count.items(), key=lambda x: (-x[1], str(x[0]).lower())
        )

        for value, count in sorted_values:
            item = QListWidgetItem(f"{value} ({count})")
            item.setData(Qt.ItemDataRole.UserRole, value)
            self.values_list.addItem(item)

        # Update stats
        total_values = len(self._values_count)
        total_usages = sum(self._values_count.values())
        self.stats_label.setText(
            say(
                "{total_values} unique values\n{total_usages} total usages",
                total_values=total_values,
                total_usages=total_usages,
            )
        )

    def _get_selected_values(self) -> list:
        """Get the selected values."""
        return [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.values_list.selectedItems()
        ]

    def _on_context_menu(self, pos):
        """Show context menu for values."""
        item = self.values_list.itemAt(pos)
        if not item:
            return

        value = item.data(Qt.ItemDataRole.UserRole)
        menu = LeftClickMenu(self)

        menu.addAction(say("Delete"), lambda: self._delete_values([value]))
        menu.addAction(say("Rename..."), lambda: self._rename_value(value))
        menu.addSeparator()
        menu.addAction(say("Copy Value"), lambda: self._copy_value(value))

        menu.exec(self.values_list.mapToGlobal(pos))

    def _on_modifier_clicked(self):
        self._on_apply_modifier(self.sender().property("mod_name"))

    def _on_delete(self):
        """Delete selected values."""
        values = self._get_selected_values()
        if not values:
            QMessageBox.information(
                self, say("No Selection"), say("Please select values to delete.")
            )
            return

        self._delete_values(values)

    def _set_action_buttons_enabled(self, enabled: bool):
        """Enable or disable all action buttons."""
        self.btn_delete.setEnabled(enabled)
        self.btn_rename.setEnabled(enabled)
        for btn in self._modifier_buttons:
            btn.setEnabled(enabled)

    def _delete_values(self, values: list):
        """Delete the given values from all videos."""
        count = len(values)
        reply = QMessageBox.question(
            self,
            say("Delete Values"),
            say(
                "Delete {count} value(s) from all videos?\n\n"
                "This will remove these values from every video that has them.",
                count=count,
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._set_action_buttons_enabled(False)
            try:
                self.ctx.delete_property_values(self.prop_name, values)
                self._modified = True
                self._load_values()
            except Exception as e:
                QMessageBox.warning(
                    self, say("Error"), say("Failed to delete values: {error}", error=e)
                )
            finally:
                self._set_action_buttons_enabled(True)

    def _on_rename(self):
        """Rename a selected value."""
        values = self._get_selected_values()
        if len(values) != 1:
            QMessageBox.information(
                self,
                say("Select One"),
                say("Please select exactly one value to rename."),
            )
            return

        self._rename_value(values[0])

    def _rename_value(self, old_value):
        """Rename a value (merges if target exists)."""
        text, ok = QInputDialog.getText(
            self,
            say("Rename Value"),
            say("Rename '{old_value}' to:", old_value=old_value),
            text=str(old_value),
        )

        if not ok or not text.strip():
            return

        text = text.strip()
        if text == str(old_value):
            return

        # The backend validates values against the property type, so the typed
        # text has to be converted before it is sent (and before it is compared
        # to the existing, already-typed values).
        try:
            new_value = PROP_UNIT_CONVERTER[self.prop_type.type](text)
        except ValueError:
            QMessageBox.warning(
                self,
                say("Error"),
                say(
                    "Invalid value for type {prop_type}: {value}",
                    prop_type=self.prop_type.type,
                    value=text,
                ),
            )
            return

        if new_value == old_value:
            return

        # Check if merging
        if new_value in self._values_count:
            reply = QMessageBox.question(
                self,
                say("Merge Values"),
                say(
                    "'{new_value}' already exists. Merge '{old_value}' into it?",
                    new_value=new_value,
                    old_value=old_value,
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            self.ctx.replace_property_values(self.prop_name, [old_value], new_value)
            self._modified = True
            self._load_values()
        except Exception as e:
            QMessageBox.warning(
                self, say("Error"), say("Failed to rename value: {error}", error=e)
            )

    def _on_apply_modifier(self, modifier: str):
        """Apply a modifier to all property values."""
        reply = QMessageBox.question(
            self,
            say("Apply {modifier}", modifier=modifier.title()),
            say(
                "Apply '{modifier}' to ALL values of '{prop_name}'?\n\n"
                "This will modify values across all videos.",
                modifier=modifier,
                prop_name=self.prop_name,
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._set_action_buttons_enabled(False)
            try:
                self.ctx.apply_on_prop_value(self.prop_name, modifier)
                self._modified = True
                self._load_values()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    say("Error"),
                    say("Failed to apply modifier: {error}", error=e),
                )
            finally:
                self._set_action_buttons_enabled(True)

    def _copy_value(self, value):
        """Copy value to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(str(value))

    def was_modified(self) -> bool:
        """Return whether any changes were made."""
        return self._modified
