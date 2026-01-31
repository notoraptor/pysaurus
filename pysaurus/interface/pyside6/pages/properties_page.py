"""
Properties page for managing video properties.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pysaurus.interface.pyside6.app_context import AppContext


class PropertiesPage(QWidget):
    """
    Page for managing video properties.

    Features:
    - View all properties with details (name, type, default, multiple, enum)
    - Create new properties
    - Rename, delete, convert properties
    - Manage property values
    - Fill property with terms
    - Move values between properties
    """

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._prop_types: list = []
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header with back button
        header_layout = QHBoxLayout()

        self.btn_back = QPushButton("< Back to Videos")
        self.btn_back.clicked.connect(self._on_back)
        header_layout.addWidget(self.btn_back)

        header_layout.addStretch()

        title_label = QLabel("<b>Property Management</b>")
        title_label.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Main content with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel: properties table and actions
        left_panel = self._create_properties_panel()
        splitter.addWidget(left_panel)

        # Right panel: create new property
        right_panel = self._create_new_property_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([600, 300])

    def _create_properties_panel(self) -> QWidget:
        """Create the panel showing existing properties."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Section header
        header = QHBoxLayout()
        header.addWidget(QLabel("<b>Existing Properties</b>"))
        header.addStretch()

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh)
        header.addWidget(self.btn_refresh)

        layout.addLayout(header)

        # Properties table
        self.props_table = QTableWidget()
        self.props_table.setColumnCount(6)
        self.props_table.setHorizontalHeaderLabels(
            ["Name", "Type", "Default", "Multiple", "Enum", "Actions"]
        )
        self.props_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.props_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.props_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.props_table.setAlternatingRowColors(True)
        layout.addWidget(self.props_table)

        # Bulk actions
        actions_frame = QFrame()
        actions_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(5, 5, 5, 5)

        actions_layout.addWidget(QLabel("Advanced:"))

        self.btn_fill_terms = QPushButton("Fill with Terms...")
        self.btn_fill_terms.setToolTip(
            "Fill a property with terms extracted from video titles"
        )
        self.btn_fill_terms.clicked.connect(self._on_fill_with_terms)
        actions_layout.addWidget(self.btn_fill_terms)

        actions_layout.addStretch()

        layout.addWidget(actions_frame)

        return panel

    def _create_new_property_panel(self) -> QWidget:
        """Create the panel for adding new properties."""
        panel = QGroupBox("Create New Property")
        layout = QVBoxLayout(panel)

        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Property name")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["str", "int", "float", "bool"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # Multiple
        self.multiple_check = QCheckBox("Allow multiple values")
        self.multiple_check.setToolTip(
            "If enabled, videos can have multiple values for this property.\n"
            "Only available for string type."
        )
        layout.addWidget(self.multiple_check)

        # Enumeration
        self.enum_check = QCheckBox("Use enumeration")
        self.enum_check.setToolTip(
            "If enabled, only predefined values can be used.\n"
            "Enter values below, one per line."
        )
        self.enum_check.toggled.connect(self._on_enum_toggled)
        layout.addWidget(self.enum_check)

        # Enum values
        enum_label = QLabel("Enum values (one per line):")
        layout.addWidget(enum_label)

        self.enum_input = QLineEdit()
        self.enum_input.setPlaceholderText("value1, value2, value3")
        self.enum_input.setEnabled(False)
        layout.addWidget(self.enum_input)

        # Default
        default_layout = QHBoxLayout()
        default_layout.addWidget(QLabel("Default:"))
        self.default_input = QLineEdit()
        self.default_input.setPlaceholderText("Default value")
        default_layout.addWidget(self.default_input)
        layout.addLayout(default_layout)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.clicked.connect(self._reset_form)
        btn_layout.addWidget(self.btn_reset)

        self.btn_create = QPushButton("Create Property")
        self.btn_create.setStyleSheet("font-weight: bold;")
        self.btn_create.clicked.connect(self._on_create)
        btn_layout.addWidget(self.btn_create)

        layout.addLayout(btn_layout)

        return panel

    def _on_type_changed(self, type_name: str):
        """Handle type change - enable/disable multiple option."""
        # Multiple only makes sense for str
        is_string = type_name == "str"
        self.multiple_check.setEnabled(is_string)
        if not is_string:
            self.multiple_check.setChecked(False)

        # Enum only for str
        self.enum_check.setEnabled(is_string)
        if not is_string:
            self.enum_check.setChecked(False)

    def _on_enum_toggled(self, checked: bool):
        """Handle enum checkbox toggle."""
        self.enum_input.setEnabled(checked)

    def _reset_form(self):
        """Reset the new property form."""
        self.name_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.multiple_check.setChecked(False)
        self.enum_check.setChecked(False)
        self.enum_input.clear()
        self.default_input.clear()

    def refresh(self):
        """Refresh the properties list."""
        if not self.ctx.database:
            return

        self._prop_types = self.ctx.database.get_prop_types()
        self.props_table.setRowCount(len(self._prop_types))

        for i, prop_type in enumerate(self._prop_types):
            name = prop_type.get("name", "")
            ptype = prop_type.get("type", "str")  # String like "str", "int", etc.
            default_values = prop_type.get("defaultValues", [])
            default = default_values[0] if default_values else None
            multiple = prop_type.get("multiple", False)
            enumeration = prop_type.get("enumeration")

            # Name
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.props_table.setItem(i, 0, name_item)

            # Type
            type_item = QTableWidgetItem(str(ptype))
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.props_table.setItem(i, 1, type_item)

            # Default
            default_str = str(default) if default is not None else ""
            default_item = QTableWidgetItem(default_str)
            default_item.setFlags(default_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.props_table.setItem(i, 2, default_item)

            # Multiple
            multiple_item = QTableWidgetItem("Yes" if multiple else "No")
            multiple_item.setFlags(multiple_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if multiple:
                multiple_item.setForeground(Qt.GlobalColor.darkGreen)
            self.props_table.setItem(i, 3, multiple_item)

            # Enum
            if enumeration:
                enum_str = ", ".join(str(v) for v in enumeration[:3])
                if len(enumeration) > 3:
                    enum_str += f"... ({len(enumeration)})"
            else:
                enum_str = "-"
            enum_item = QTableWidgetItem(enum_str)
            enum_item.setFlags(enum_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.props_table.setItem(i, 4, enum_item)

            # Actions
            actions_widget = self._create_actions_widget(prop_type)
            self.props_table.setCellWidget(i, 5, actions_widget)

        self.props_table.resizeColumnsToContents()

    def _create_actions_widget(self, prop_type: dict) -> QWidget:
        """Create the actions widget for a property row."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        name = prop_type.get("name", "")
        ptype = prop_type.get("type", "str")  # String like "str", "int", etc.
        multiple = prop_type.get("multiple", False)

        # Values button (only for string properties)
        if ptype == "str":
            btn_values = QPushButton("Values")
            btn_values.setFixedWidth(60)
            btn_values.setToolTip("Manage property values")
            btn_values.clicked.connect(lambda _, n=name: self._on_manage_values(n))
            layout.addWidget(btn_values)

        # Rename button
        btn_rename = QPushButton("Rename")
        btn_rename.setFixedWidth(60)
        btn_rename.clicked.connect(lambda _, n=name: self._on_rename(n))
        layout.addWidget(btn_rename)

        # Convert button (only for string properties)
        if ptype is str:
            convert_text = "Single" if multiple else "Multi"
            btn_convert = QPushButton(convert_text)
            btn_convert.setFixedWidth(50)
            btn_convert.setToolTip(
                "Convert to single value" if multiple else "Convert to multiple values"
            )
            btn_convert.clicked.connect(
                lambda _, n=name, m=multiple: self._on_convert(n, m)
            )
            layout.addWidget(btn_convert)

        # Move values button (only for string-multiple)
        if ptype is str and multiple:
            btn_move = QPushButton("Move")
            btn_move.setFixedWidth(50)
            btn_move.setToolTip("Move values to another property")
            btn_move.clicked.connect(lambda _, n=name: self._on_move_values(n))
            layout.addWidget(btn_move)

        # Delete button
        btn_delete = QPushButton("Del")
        btn_delete.setFixedWidth(40)
        btn_delete.setStyleSheet("color: #c00;")
        btn_delete.clicked.connect(lambda _, n=name: self._on_delete(n))
        layout.addWidget(btn_delete)

        return widget

    def _on_back(self):
        """Navigate back to videos page."""
        main_window = self.window()
        if hasattr(main_window, "show_videos_page"):
            main_window.show_videos_page()

    def _on_create(self):
        """Create a new property."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a property name.")
            return

        type_name = self.type_combo.currentText()
        type_map = {"bool": bool, "int": int, "float": float, "str": str}
        prop_type = type_map[type_name]

        multiple = self.multiple_check.isChecked()

        # Parse default value
        default_text = self.default_input.text().strip()
        try:
            if type_name == "bool":
                default = (
                    default_text.lower() in ("true", "1", "yes")
                    if default_text
                    else False
                )
            elif type_name == "int":
                default = int(default_text) if default_text else 0
            elif type_name == "float":
                default = float(default_text) if default_text else 0.0
            else:
                default = default_text
        except ValueError:
            QMessageBox.warning(
                self, "Error", f"Invalid default value for type {type_name}."
            )
            return

        # Handle enumeration
        definition = default
        if self.enum_check.isChecked() and type_name == "str":
            enum_text = self.enum_input.text().strip()
            if enum_text:
                enum_values = [v.strip() for v in enum_text.split(",") if v.strip()]
                if enum_values:
                    definition = enum_values

        try:
            self.ctx.database.prop_type_add(name, prop_type, definition, multiple)
            self._reset_form()
            self.refresh()
            QMessageBox.information(
                self, "Success", f"Property '{name}' created successfully."
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create property: {e}")

    def _on_rename(self, name: str):
        """Rename a property."""
        from PySide6.QtWidgets import QInputDialog

        new_name, ok = QInputDialog.getText(
            self, "Rename Property", f"Enter new name for '{name}':", text=name
        )

        if not ok or not new_name.strip():
            return

        new_name = new_name.strip()
        if new_name == name:
            return

        try:
            self.ctx.database.prop_type_set_name(name, new_name)
            self.refresh()
            QMessageBox.information(
                self, "Success", f"Property renamed to '{new_name}'."
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to rename property: {e}")

    def _on_delete(self, name: str):
        """Delete a property."""
        reply = QMessageBox.question(
            self,
            "Delete Property",
            f"Are you sure you want to delete property '{name}'?\n\n"
            "This will remove all values for this property from all videos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.ctx.database.prop_type_del(name)
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete property: {e}")

    def _on_convert(self, name: str, currently_multiple: bool):
        """Convert property between single and multiple."""
        target = "single value" if currently_multiple else "multiple values"
        reply = QMessageBox.question(
            self,
            "Convert Property",
            f"Convert '{name}' to {target}?\n\n"
            f"{'Values will be merged.' if currently_multiple else 'Existing values will become lists.'}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.ctx.database.prop_type_set_multiple(name, not currently_multiple)
                self.refresh()
                QMessageBox.information(
                    self, "Success", f"Property '{name}' converted to {target}."
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to convert property: {e}")

    def _on_manage_values(self, name: str):
        """Open the values management dialog."""
        from pysaurus.interface.pyside6.dialogs.property_values_dialog import (
            PropertyValuesDialog,
        )

        # Find the property type
        prop_type = next(
            (pt for pt in self._prop_types if pt.get("name") == name), None
        )
        if not prop_type:
            return

        dialog = PropertyValuesDialog(name, prop_type, self.ctx.database, self)
        dialog.exec()

        if dialog.was_modified():
            self.refresh()

    def _on_move_values(self, name: str):
        """Open the move values dialog."""
        from pysaurus.interface.pyside6.dialogs.move_values_dialog import (
            MoveValuesDialog,
        )

        # Find the property type
        prop_type = next(
            (pt for pt in self._prop_types if pt.get("name") == name), None
        )
        if not prop_type:
            return

        dialog = MoveValuesDialog(prop_type, self._prop_types, self.ctx.database, self)
        if dialog.exec():
            values, target_prop, concatenate = dialog.get_result()
            if values and target_prop:
                try:
                    count = self.ctx.algos.move_property_values(
                        values, name, target_prop["name"], concatenate=concatenate
                    )
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Moved values for {count} videos from '{name}' to '{target_prop['name']}'.",
                    )
                    self.refresh()
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to move values: {e}")

    def _on_fill_with_terms(self):
        """Fill a property with terms extracted from video titles."""
        from pysaurus.interface.pyside6.dialogs.fill_property_dialog import (
            FillPropertyDialog,
        )

        dialog = FillPropertyDialog(self._prop_types, self)
        if dialog.exec():
            prop_type, only_empty = dialog.get_result()
            if prop_type:
                reply = QMessageBox.question(
                    self,
                    "Fill Property",
                    f"Fill '{prop_type['name']}' with terms extracted from video filenames?\n\n"
                    f"{'Only videos without values will be affected.' if only_empty else 'All videos will be affected.'}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )

                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        self.ctx.algos.fill_property_with_terms(
                            prop_type["name"], only_empty=only_empty
                        )
                        QMessageBox.information(
                            self,
                            "Success",
                            f"Property '{prop_type['name']}' filled with terms.",
                        )
                        self.refresh()
                    except Exception as e:
                        QMessageBox.warning(
                            self, "Error", f"Failed to fill property: {e}"
                        )
