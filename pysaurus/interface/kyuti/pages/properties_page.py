"""
Properties page for managing video properties.
"""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.language import say
from pysaurus.interface.common.prop_format import (
    format_prop_domain,
    format_prop_literal,
)
from pysaurus.interface.kyuti.app_context import AppContext
from pysaurus.interface.kyuti.dialogs.fill_property_dialog import FillPropertyDialog
from pysaurus.interface.kyuti.dialogs.move_values_dialog import MoveValuesDialog
from pysaurus.interface.kyuti.dialogs.property_values_dialog import PropertyValuesDialog
from pysaurus.interface.kyuti.widgets.bool_value_widget import BoolValueWidget
from pysaurus.properties.properties import (
    OPEN_DOMAIN_PROP_TYPES,
    PROP_UNIT_CONVERTER,
    PropRawType,
    PropType,
    PropUnitType,
)


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

        # Header with back button (compact)
        header_widget = QWidget()
        header_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 5)

        self.btn_back = QPushButton(say("< Back to Videos"))
        self.btn_back.clicked.connect(self._on_back)
        header_layout.addWidget(self.btn_back)

        header_layout.addStretch()

        self._title_label = QLabel("<b>" + say("Property Management") + "</b>")
        self._title_label.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(self._title_label)

        header_layout.addStretch()

        layout.addWidget(header_widget)

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
        self._existing_props_label = QLabel("<b>" + say("Existing Properties") + "</b>")
        header.addWidget(self._existing_props_label)
        header.addStretch()

        self.btn_refresh = QPushButton(say("Refresh"))
        self.btn_refresh.clicked.connect(self.refresh)
        header.addWidget(self.btn_refresh)

        layout.addLayout(header)

        # Properties table
        self.props_table = QTableWidget()
        self.props_table.setColumnCount(6)
        self.props_table.setHorizontalHeaderLabels(
            [
                say("Name"),
                say("Type"),
                say("Default"),
                say("Multiple"),
                say("Enum"),
                say("Actions"),
            ]
        )
        self.props_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.props_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.props_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        # Let Actions column resize to its content
        self.props_table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )
        self.props_table.setAlternatingRowColors(True)
        layout.addWidget(self.props_table)

        # Bulk actions
        actions_frame = QFrame()
        actions_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(5, 5, 5, 5)

        self._advanced_label = QLabel(say("Advanced:"))
        actions_layout.addWidget(self._advanced_label)

        self.btn_fill_terms = QPushButton(say("Fill with Terms..."))
        self.btn_fill_terms.setToolTip(
            say("Fill a property with terms extracted from video titles")
        )
        self.btn_fill_terms.clicked.connect(self._on_fill_with_terms)
        actions_layout.addWidget(self.btn_fill_terms)

        actions_layout.addStretch()

        layout.addWidget(actions_frame)

        return panel

    def _create_new_property_panel(self) -> QWidget:
        """Create the panel for adding new properties."""
        self._new_property_group = QGroupBox(say("Create New Property"))
        layout = QVBoxLayout(self._new_property_group)

        # Name
        name_layout = QHBoxLayout()
        self._name_label = QLabel(say("Name:"))
        name_layout.addWidget(self._name_label)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(say("Property name"))
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Type
        type_layout = QHBoxLayout()
        self._type_label = QLabel(say("Type:"))
        type_layout.addWidget(self._type_label)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["str", "int", "float", "bool"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # Multiple
        self.multiple_check = QCheckBox(say("Allow multiple values"))
        self.multiple_check.setToolTip(
            say(
                "If enabled, videos can have multiple values for this property.\n"
                "Not available for boolean properties."
            )
        )
        self.multiple_check.toggled.connect(self._update_default_field)
        layout.addWidget(self.multiple_check)

        # Enumeration
        self.enum_check = QCheckBox(say("Use enumeration"))
        self.enum_check.setToolTip(
            say(
                "If enabled, only predefined values can be used.\n"
                "The first value entered below becomes the default one.\n"
                "Not available for boolean properties."
            )
        )
        self.enum_check.toggled.connect(self._on_enum_toggled)
        layout.addWidget(self.enum_check)

        # Enum values
        self._enum_label = QLabel(say("Enum values (comma-separated):"))
        layout.addWidget(self._enum_label)

        self.enum_input = QLineEdit()
        self.enum_input.setEnabled(False)
        layout.addWidget(self.enum_input)

        # Default
        default_layout = QHBoxLayout()
        self._default_label = QLabel(say("Default:"))
        default_layout.addWidget(self._default_label)
        self.default_input = QLineEdit()
        default_layout.addWidget(self.default_input)
        # A bool picks its default out of its implicit two-value domain instead
        # of typing it: reading a bool back from free text would have to match
        # the language the user typed in. Only one of the two is ever shown.
        self.default_bool_input = BoolValueWidget(with_undefined=False)
        default_layout.addWidget(self.default_bool_input)
        layout.addLayout(default_layout)

        # Type drives which options are offered; apply it to the initial type.
        self._on_type_changed(self.type_combo.currentText())

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_reset = QPushButton(say("Reset"))
        self.btn_reset.clicked.connect(self._reset_form)
        btn_layout.addWidget(self.btn_reset)

        self.btn_create = QPushButton(say("Create Property"))
        self.btn_create.setStyleSheet("font-weight: bold;")
        self.btn_create.clicked.connect(self._on_create)
        btn_layout.addWidget(self.btn_create)

        layout.addLayout(btn_layout)

        return self._new_property_group

    def retranslateUi(self):
        """Re-apply the text of every *static* piece of chrome in the current
        language. Triggered by QEvent.LanguageChange (see changeEvent).

        The construction keeps its say() calls (the text stays readable at the
        call site), so this only *repeats* them for the persistent widgets; it
        is deliberately NOT called at startup. Dynamic content (the properties
        table rows and their per-row action menus, rebuilt by refresh()) is
        retranslated on its own via the state_changed signal.
        """
        # Header
        self.btn_back.setText(say("< Back to Videos"))
        self._title_label.setText("<b>" + say("Property Management") + "</b>")
        # Existing-properties panel
        self._existing_props_label.setText("<b>" + say("Existing Properties") + "</b>")
        self.btn_refresh.setText(say("Refresh"))
        self.props_table.setHorizontalHeaderLabels(
            [
                say("Name"),
                say("Type"),
                say("Default"),
                say("Multiple"),
                say("Enum"),
                say("Actions"),
            ]
        )
        self._advanced_label.setText(say("Advanced:"))
        self.btn_fill_terms.setText(say("Fill with Terms..."))
        self.btn_fill_terms.setToolTip(
            say("Fill a property with terms extracted from video titles")
        )
        # Create-new-property panel
        self._new_property_group.setTitle(say("Create New Property"))
        self._name_label.setText(say("Name:"))
        self.name_input.setPlaceholderText(say("Property name"))
        self._type_label.setText(say("Type:"))
        self.multiple_check.setText(say("Allow multiple values"))
        self.multiple_check.setToolTip(
            say(
                "If enabled, videos can have multiple values for this property.\n"
                "Not available for boolean properties."
            )
        )
        self.enum_check.setText(say("Use enumeration"))
        self.enum_check.setToolTip(
            say(
                "If enabled, only predefined values can be used.\n"
                "The first value entered below becomes the default one.\n"
                "Not available for boolean properties."
            )
        )
        self._enum_label.setText(say("Enum values (comma-separated):"))
        self._default_label.setText(say("Default:"))
        # Both placeholders depend on the form state, not only on the language.
        self._update_enum_placeholder()
        self._update_default_field()
        self.btn_reset.setText(say("Reset"))
        self.btn_create.setText(say("Create Property"))

    def changeEvent(self, event):
        """Qt posts LanguageChange to every widget when a QTranslator is
        installed or removed. That is our cue to re-pull the static chrome."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def _on_type_changed(self, type_name: str):
        """Handle type change - offer multiple/enumeration where they apply."""
        # Both options only carry information for open-domain types (str, int,
        # float); a bool already *is* its own two-value enumeration.
        open_domain = type_name in OPEN_DOMAIN_PROP_TYPES
        self.multiple_check.setEnabled(open_domain)
        self.enum_check.setEnabled(open_domain)
        if not open_domain:
            self.multiple_check.setChecked(False)
            self.enum_check.setChecked(False)

        self._update_enum_placeholder()
        self._update_default_field()

    def _on_enum_toggled(self, checked: bool):
        """Handle enum checkbox toggle."""
        self.enum_input.setEnabled(checked)
        self._update_default_field()

    def _update_enum_placeholder(self):
        """Show an example matching the selected type in the enum field."""
        examples = {
            "str": say("value1, value2, value3"),
            "int": "1, 2, 3",
            "float": "1.5, 2.5",
        }
        self.enum_input.setPlaceholderText(
            examples.get(self.type_combo.currentText(), "")
        )

    def _update_default_field(self):
        """Only let the default be typed in when it is actually used.

        A multiple property has no default (PropType.define forces an empty
        list), and an enumerated one takes its first enum value as default. In
        both cases the field would be silently ignored, so it is cleared and
        disabled instead, with a placeholder saying where the default comes from.
        """
        multiple = self.multiple_check.isChecked()
        enumerated = self.enum_check.isChecked()
        # A bool is never multiple nor enumerated, so its picker is always the
        # one shown, and always usable.
        is_bool = self.type_combo.currentText() == "bool"
        self.default_input.setVisible(not is_bool)
        self.default_bool_input.setVisible(is_bool)

        if multiple:
            self.default_input.setPlaceholderText(
                say("No default value for a multiple property")
            )
        elif enumerated:
            self.default_input.setPlaceholderText(say("First enumeration value"))
        else:
            self.default_input.setPlaceholderText(say("Default value"))

        editable = not multiple and not enumerated
        if not editable:
            self.default_input.clear()
        self.default_input.setEnabled(editable)

    def _reset_form(self):
        """Reset the new property form."""
        self.name_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.multiple_check.setChecked(False)
        self.enum_check.setChecked(False)
        self.enum_input.clear()
        self.default_input.clear()
        self.default_bool_input.set_value(False)

    def refresh(self):
        """Refresh the properties list."""
        if not self.ctx.has_database():
            return

        self._prop_types = self.ctx.get_prop_types()
        self.props_table.setRowCount(len(self._prop_types))

        for i, prop_type in enumerate(self._prop_types):
            name = prop_type.name
            ptype = prop_type.type  # String like "str", "int", etc.
            default_values = prop_type.default
            default = default_values[0] if default_values else None
            multiple = prop_type.multiple

            # Name
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.props_table.setItem(i, 0, name_item)

            # Type
            type_item = QTableWidgetItem(str(ptype))
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.props_table.setItem(i, 1, type_item)

            # Default
            default_str = (
                format_prop_literal(prop_type, default) if default is not None else ""
            )
            default_item = QTableWidgetItem(default_str)
            default_item.setFlags(default_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.props_table.setItem(i, 2, default_item)

            # Multiple
            multiple_item = QTableWidgetItem(say("Yes") if multiple else say("No"))
            multiple_item.setFlags(multiple_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if multiple:
                multiple_item.setForeground(Qt.GlobalColor.darkGreen)
            self.props_table.setItem(i, 3, multiple_item)

            # Enum: a bool has no stored enumeration but still has a domain,
            # so this shows the implicit one rather than a dash.
            domain = format_prop_domain(prop_type)
            if domain:
                enum_str = ", ".join(domain[:3])
                if len(domain) > 3:
                    enum_str += f"... ({len(domain)})"
            else:
                enum_str = "-"
            enum_item = QTableWidgetItem(enum_str)
            enum_item.setFlags(enum_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.props_table.setItem(i, 4, enum_item)

            # Actions
            actions_widget = self._create_actions_widget(prop_type)
            self.props_table.setCellWidget(i, 5, actions_widget)

        self.props_table.resizeColumnsToContents()

    def _create_actions_widget(self, prop_type: PropType) -> QWidget:
        """Create the actions widget for a property row."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        name = prop_type.name
        ptype = prop_type.type  # String like "str", "int", etc.
        multiple = prop_type.multiple
        is_string = ptype == "str"
        # A bool has nothing to manage or convert: no value set to curate, and
        # "multiple" is not offered for it (see OPEN_DOMAIN_PROP_TYPES).
        open_domain = ptype in OPEN_DOMAIN_PROP_TYPES

        # Create dropdown button with menu
        btn_actions = QPushButton(say("Actions"))

        menu = QMenu(btn_actions)

        # Values action (only for open-domain properties)
        if open_domain:
            action_values = menu.addAction(say("Manage Values..."))
            action_values.setProperty("prop_name", name)
            action_values.triggered.connect(self._on_action_manage_values)

        # Rename action (always)
        action_rename = menu.addAction(say("Rename..."))
        action_rename.setProperty("prop_name", name)
        action_rename.triggered.connect(self._on_action_rename)

        # Convert action (only for open-domain properties)
        if open_domain:
            convert_text = (
                say("Convert to Single Value")
                if multiple
                else say("Convert to Multiple Values")
            )
            action_convert = menu.addAction(convert_text)
            action_convert.setProperty("prop_name", name)
            action_convert.setProperty("currently_multiple", multiple)
            action_convert.triggered.connect(self._on_action_convert)

        # Move values action (only for string-multiple: DatabaseAlgorithms
        # .move_property_values asserts a str target and joins values as text)
        if is_string and multiple:
            action_move = menu.addAction(say("Move Values..."))
            action_move.setProperty("prop_name", name)
            action_move.triggered.connect(self._on_action_move_values)

        # Separator before delete
        menu.addSeparator()

        # Delete action (always)
        action_delete = menu.addAction(say("Delete"))
        action_delete.setProperty("prop_name", name)
        action_delete.triggered.connect(self._on_action_delete)

        btn_actions.setMenu(menu)
        layout.addWidget(btn_actions)

        return widget

    def _on_action_manage_values(self):
        self._on_manage_values(self.sender().property("prop_name"))

    def _on_action_rename(self):
        self._on_rename(self.sender().property("prop_name"))

    def _on_action_convert(self):
        sender = self.sender()
        self._on_convert(
            sender.property("prop_name"), sender.property("currently_multiple")
        )

    def _on_action_move_values(self):
        self._on_move_values(self.sender().property("prop_name"))

    def _on_action_delete(self):
        self._on_delete(self.sender().property("prop_name"))

    def _on_back(self):
        """Navigate back to videos page."""
        main_window = self.window()
        if hasattr(main_window, "show_videos_page"):
            main_window.show_videos_page()

    def _read_definition(self, prop_type: str) -> PropRawType:
        """Build the definition to hand to the backend.

        That is either the enumeration (typed, first value being the default) or
        a single default value. Raises ValueError carrying a translated,
        user-facing message when the form holds invalid input.
        """
        if self.enum_check.isChecked():
            return self._read_enumeration(prop_type)
        return self._read_default(prop_type)

    def _read_enumeration(self, prop_type: str) -> list[PropUnitType]:
        """Parse the comma-separated enum field into typed, distinct values."""
        convert = PROP_UNIT_CONVERTER[prop_type]
        values: list[PropUnitType] = []
        for token in self.enum_input.text().split(","):
            token = token.strip()
            if not token:
                continue
            try:
                value = convert(token)
            except ValueError:
                raise ValueError(
                    say(
                        "Invalid enumeration value for type {prop_type}: {value}",
                        prop_type=prop_type,
                        value=token,
                    )
                ) from None
            # Keep the order typed in: the first value becomes the default.
            if value not in values:
                values.append(value)
        if len(values) < 2:
            raise ValueError(say("An enumeration needs at least two distinct values."))
        return values

    def _read_default(self, prop_type: str) -> PropUnitType:
        """Parse the default field, falling back to the type's empty value."""
        if prop_type == "bool":
            # Picked, never typed: the widget always has one state checked, so
            # value() is never None here -- bool() is only for the type checker.
            return bool(self.default_bool_input.value())
        default_text = self.default_input.text().strip()
        if not default_text:
            return {"int": 0, "float": 0.0, "str": ""}[prop_type]
        try:
            return PROP_UNIT_CONVERTER[prop_type](default_text)
        except ValueError:
            raise ValueError(
                say("Invalid default value for type {prop_type}.", prop_type=prop_type)
            ) from None

    def _on_create(self):
        """Create a new property."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self, say("Error"), say("Please enter a property name.")
            )
            return

        prop_type = self.type_combo.currentText()  # "bool", "int", "float", "str"

        multiple = self.multiple_check.isChecked()

        try:
            definition = self._read_definition(prop_type)
        except ValueError as exc:
            QMessageBox.warning(self, say("Error"), str(exc))
            return

        self.btn_create.setEnabled(False)
        try:
            self.ctx.create_prop_type(name, prop_type, definition, multiple)
            self._reset_form()
            QMessageBox.information(
                self,
                say("Success"),
                say("Property '{name}' created successfully.", name=name),
            )
        except Exception as e:
            QMessageBox.warning(
                self, say("Error"), say("Failed to create property: {error}", error=e)
            )
        finally:
            self.btn_create.setEnabled(True)

    def _on_rename(self, name: str):
        """Rename a property."""
        new_name, ok = QInputDialog.getText(
            self,
            say("Rename Property"),
            say("Enter new name for '{name}':", name=name),
            text=name,
        )

        if not ok or not new_name.strip():
            return

        new_name = new_name.strip()
        if new_name == name:
            return

        try:
            self.ctx.rename_prop_type(name, new_name)
            QMessageBox.information(
                self,
                say("Success"),
                say("Property renamed to '{new_name}'.", new_name=new_name),
            )
        except Exception as e:
            QMessageBox.warning(
                self, say("Error"), say("Failed to rename property: {error}", error=e)
            )

    def _on_delete(self, name: str):
        """Delete a property."""
        reply = QMessageBox.question(
            self,
            say("Delete Property"),
            say(
                "Are you sure you want to delete property '{name}'?\n\n"
                "This will remove all values for this property from all videos.",
                name=name,
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.ctx.delete_prop_type(name)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    say("Error"),
                    say("Failed to delete property: {error}", error=e),
                )

    def _on_convert(self, name: str, currently_multiple: bool):
        """Convert property between single and multiple."""
        target = say("single value") if currently_multiple else say("multiple values")
        note = (
            say("Values will be merged.")
            if currently_multiple
            else say("Existing values will become lists.")
        )
        reply = QMessageBox.question(
            self,
            say("Convert Property"),
            say("Convert '{name}' to {target}?", name=name, target=target)
            + "\n\n"
            + note,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.ctx.set_prop_type_multiple(name, not currently_multiple)
                QMessageBox.information(
                    self,
                    say("Success"),
                    say(
                        "Property '{name}' converted to {target}.",
                        name=name,
                        target=target,
                    ),
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    say("Error"),
                    say("Failed to convert property: {error}", error=e),
                )

    def _on_manage_values(self, name: str):
        """Open the values management dialog."""
        # Find the property type
        prop_type = next((pt for pt in self._prop_types if pt.name == name), None)
        if not prop_type:
            return

        dialog = PropertyValuesDialog(name, prop_type, self.ctx, self)
        dialog.exec()

    def _on_move_values(self, name: str):
        """Open the move values dialog."""
        # Find the property type
        prop_type = next((pt for pt in self._prop_types if pt.name == name), None)
        if not prop_type:
            return

        dialog = MoveValuesDialog(prop_type, self._prop_types, self.ctx, self)
        if dialog.exec():
            values, target_prop, concatenate = dialog.get_result()
            if values and target_prop:
                try:
                    count = self.ctx.move_property_values(
                        values, name, target_prop.name, concatenate=concatenate
                    )
                    QMessageBox.information(
                        self,
                        say("Success"),
                        say(
                            "Moved values for {count} videos from '{name}' to '{target_name}'.",
                            count=count,
                            name=name,
                            target_name=target_prop.name,
                        ),
                    )
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        say("Error"),
                        say("Failed to move values: {error}", error=e),
                    )

    def _on_fill_with_terms(self):
        """Fill a property with terms extracted from video titles."""
        dialog = FillPropertyDialog(self._prop_types, self)
        if dialog.exec():
            prop_type, only_empty = dialog.get_result()
            if prop_type:
                note = (
                    say("Only videos without values will be affected.")
                    if only_empty
                    else say("All videos will be affected.")
                )
                reply = QMessageBox.question(
                    self,
                    say("Fill Property"),
                    say(
                        "Fill '{name}' with terms extracted from video filenames?",
                        name=prop_type.name,
                    )
                    + "\n\n"
                    + note,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )

                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        self.ctx.fill_property_with_terms(
                            prop_type.name, only_empty=only_empty
                        )
                        QMessageBox.information(
                            self,
                            say("Success"),
                            say(
                                "Property '{name}' filled with terms.",
                                name=prop_type.name,
                            ),
                        )
                    except Exception as e:
                        QMessageBox.warning(
                            self,
                            say("Error"),
                            say("Failed to fill property: {error}", error=e),
                        )
