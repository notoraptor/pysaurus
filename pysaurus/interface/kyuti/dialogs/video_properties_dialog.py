"""
Dialog for viewing and editing video properties.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.duration import Duration
from pysaurus.core.file_size import FileSize
from pysaurus.core.language import say
from pysaurus.interface.common.common import display_geometry_text
from pysaurus.interface.kyuti.widgets.bool_value_widget import BoolValueWidget
from pysaurus.interface.kyuti.widgets.multiple_values_widget import MultipleValuesWidget
from pysaurus.properties.properties import PropType
from pysaurus.video.video_pattern import VideoPattern


class ScrollSafeComboBox(QComboBox):
    """QComboBox that ignores wheel events unless it has focus."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event: QWheelEvent):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


class ScrollSafeSpinBox(QSpinBox):
    """QSpinBox that ignores wheel events unless it has focus."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event: QWheelEvent):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


class VideoPropertiesDialog(QDialog):
    """
    Dialog for viewing video metadata and editing custom properties.

    Tabs:
    - Info: Read-only video metadata
    - Properties: Editable custom properties
    """

    def __init__(
        self, video: VideoPattern, prop_types: list[PropType], ctx, parent=None
    ):
        super().__init__(parent)
        self.video = video
        self.prop_types = prop_types
        self.ctx = ctx
        self._property_widgets: dict[str, QWidget] = {}
        self._property_labels: dict[str, QLabel] = {}
        self._clear_buttons: dict[str, QPushButton] = {}
        self._reset_buttons: dict[str, QPushButton] = {}
        self._initially_defined: dict[str, bool] = {}
        self._cleared: set[str] = set()
        self._user_modified: set[str] = set()
        self._loading = False
        self._focused_prop: str | None = None

        self.setWindowTitle(say("Properties - {title}", title=video.title))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()
        self._load_properties()

        QApplication.instance().focusChanged.connect(self._on_focus_changed)

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)

        # Tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Properties tab
        props_tab = self._create_properties_tab()
        tabs.addTab(props_tab, say("Properties"))

        # Info tab
        info_tab = self._create_info_tab()
        tabs.addTab(info_tab, say("Info"))

        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        # Disable auto-default to prevent ENTER from submitting the form
        for button in self.button_box.buttons():
            button.setAutoDefault(False)
            button.setDefault(False)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _create_info_tab(self) -> QWidget:
        """Create the info tab with video metadata."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        widget = QWidget()
        layout = QVBoxLayout(widget)

        # File info
        file_group = QGroupBox(say("File"))
        file_layout = QFormLayout(file_group)

        file_layout.addRow(say("Title:"), QLabel(str(self.video.title)))
        file_layout.addRow(say("Filename:"), QLabel(str(self.video.filename)))
        file_layout.addRow(say("Size:"), QLabel(str(FileSize(self.video.file_size))))
        file_layout.addRow(
            say("Date Modified:"), QLabel(str(self.video.date_entry_modified))
        )

        layout.addWidget(file_group)

        # Video info
        video_group = QGroupBox(say("Video"))
        video_layout = QFormLayout(video_group)

        duration = Duration(int(self.video.duration * 1_000_000))
        video_layout.addRow(say("Duration:"), QLabel(str(duration)))
        resolution = f"{self.video.width}x{self.video.height}"
        display_geometry = display_geometry_text(self.video)
        if display_geometry:
            resolution = f"{resolution} ({display_geometry})"
        video_layout.addRow(say("Resolution:"), QLabel(resolution))
        video_layout.addRow(
            say("Codec:"),
            QLabel(
                str(self.video.video_codec) if self.video.video_codec else say("N/A")
            ),
        )
        video_layout.addRow(
            say("Codec Description:"),
            QLabel(
                str(self.video.video_codec_description)
                if self.video.video_codec_description
                else say("N/A")
            ),
        )
        video_layout.addRow(
            say("Container:"),
            QLabel(
                str(self.video.container_format)
                if self.video.container_format
                else say("N/A")
            ),
        )

        # Frame rate
        if self.video.frame_rate_den and self.video.frame_rate_den > 0:
            fps = self.video.frame_rate_num / self.video.frame_rate_den
            video_layout.addRow(
                say("Frame Rate:"), QLabel(say("{fps:.2f} fps", fps=fps))
            )

        layout.addWidget(video_group)

        # Audio info
        audio_group = QGroupBox(say("Audio"))
        audio_layout = QFormLayout(audio_group)

        audio_layout.addRow(
            say("Codec:"),
            QLabel(
                str(self.video.audio_codec) if self.video.audio_codec else say("N/A")
            ),
        )
        audio_layout.addRow(
            say("Channels:"),
            QLabel(str(self.video.channels) if self.video.channels else say("N/A")),
        )
        audio_layout.addRow(
            say("Sample Rate:"),
            QLabel(
                say("{sample_rate} Hz", sample_rate=self.video.sample_rate)
                if self.video.sample_rate
                else say("N/A")
            ),
        )
        audio_layout.addRow(
            say("Bit Rate:"),
            QLabel(
                say("{bit_rate}/s", bit_rate=self.video.audio_bit_rate_formatted)
                if self.video.audio_bit_rate
                else say("N/A")
            ),
        )

        layout.addWidget(audio_group)

        # Status
        status_group = QGroupBox(say("Status"))
        status_layout = QFormLayout(status_group)

        status_layout.addRow(
            say("Found:"), QLabel(say("Yes") if self.video.found else say("No"))
        )
        status_layout.addRow(
            say("Readable:"), QLabel(say("No") if self.video.unreadable else say("Yes"))
        )
        status_layout.addRow(
            say("Has Thumbnail:"),
            QLabel(say("Yes") if self.video.with_thumbnails else say("No")),
        )

        if self.video.similarity_id is not None:
            status_layout.addRow(
                say("Similarity Group:"), QLabel(str(self.video.similarity_id))
            )
        if self.video.similarity_id_reencoded is not None:
            status_layout.addRow(
                say("Re-encoded Group:"),
                QLabel(str(self.video.similarity_id_reencoded)),
            )

        layout.addWidget(status_group)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    def _create_properties_tab(self) -> QWidget:
        """Create the properties tab with editable custom properties."""
        if not self.prop_types:
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.addWidget(QLabel(say("No custom properties defined.")))
            layout.addStretch()
            return widget

        # Splitter: property list (left) + scrollable form (right)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: property name list (table of contents)
        self._prop_list = QListWidget()
        for prop_type in self.prop_types:
            self._prop_list.addItem(prop_type.name)
        self._prop_list.currentRowChanged.connect(self._on_prop_list_selection)
        splitter.addWidget(self._prop_list)

        # Right: scrollable form with all properties
        self._props_scroll = QScrollArea()
        self._props_scroll.setWidgetResizable(True)

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)

        self._property_sections: dict[str, QWidget] = {}

        for i, prop_type in enumerate(self.prop_types):
            name = prop_type.name

            # Section: label on top, widget below, alternating background
            section = QWidget()
            section.setAutoFillBackground(True)
            if i % 2 == 1:
                palette = section.palette()
                base = palette.color(QPalette.ColorRole.Window)
                palette.setColor(QPalette.ColorRole.Window, base.darker(107))
                section.setPalette(palette)

            section_layout = QVBoxLayout(section)
            section_layout.setContentsMargins(8, 8, 8, 16)
            section_layout.setSpacing(4)

            # Label as section header
            label_text = name
            detail_parts = []
            if prop_type.multiple:
                detail_parts.append(say("multiple"))
            if prop_type.enumeration:
                detail_parts.append(say("enum"))
            if detail_parts:
                label_text += f"  ({', '.join(detail_parts)})"

            label = QLabel(label_text)
            font = label.font()
            font.setPointSize(font.pointSize() + 2)
            label.setFont(font)
            self._property_labels[name] = label
            section_layout.addWidget(label)

            if prop_type.multiple:
                prop_widget = MultipleValuesWidget(prop_type)
                self._property_widgets[name] = prop_widget
                section_layout.addWidget(prop_widget)
            else:
                # Single property: input widget + Clear button
                container = QWidget()
                h_layout = QHBoxLayout(container)
                h_layout.setContentsMargins(0, 0, 0, 0)
                h_layout.setSpacing(4)

                input_widget = self._create_single_property_widget(prop_type)
                h_layout.addWidget(input_widget, 1)

                reset_btn = QPushButton(say("Reset"))
                reset_btn.setToolTip(say("Restore initial value of {name}", name=name))
                reset_btn.setFixedWidth(50)
                reset_btn.clicked.connect(
                    lambda _checked, n=name: self._on_reset_property(n)
                )
                reset_btn.setVisible(False)
                h_layout.addWidget(reset_btn)

                clear_btn = QPushButton(say("Clear"))
                clear_btn.setToolTip(
                    say("Remove {name} value from this video", name=name)
                )
                clear_btn.setFixedWidth(50)
                clear_btn.clicked.connect(
                    lambda _checked, n=name: self._on_clear_property(n)
                )
                clear_btn.setVisible(False)
                h_layout.addWidget(clear_btn)

                self._property_widgets[name] = input_widget
                self._reset_buttons[name] = reset_btn
                self._clear_buttons[name] = clear_btn
                section_layout.addWidget(container)

            form_layout.addWidget(section)
            self._property_sections[name] = section

        form_layout.addStretch()
        self._props_scroll.setWidget(form_widget)
        splitter.addWidget(self._props_scroll)

        splitter.setSizes([150, 350])
        return splitter

    def _on_prop_list_selection(self, row: int):
        """Scroll the properties form to the selected property and focus it."""
        if row < 0 or row >= len(self.prop_types):
            return
        name = self.prop_types[row].name
        section = self._property_sections.get(name)
        if section:
            self._props_scroll.ensureWidgetVisible(section)
        widget = self._property_widgets.get(name)
        if widget:
            if isinstance(widget, MultipleValuesWidget):
                if widget.enumeration:
                    first_cb = next(iter(widget.checkboxes.values()), None)
                    if first_cb:
                        first_cb.setFocus()
                else:
                    widget.input_edit.setFocus()
            else:
                widget.setFocus()

    def _on_focus_changed(self, _old, new):
        """Bold the label of the property whose widget has focus."""
        focused_prop = None
        if new is not None:
            for name, section in self._property_sections.items():
                if new is section or section.isAncestorOf(new):
                    focused_prop = name
                    break
        if focused_prop != self._focused_prop:
            # Unbold previous
            if self._focused_prop:
                label = self._property_labels.get(self._focused_prop)
                if label:
                    font = label.font()
                    font.setBold(False)
                    label.setFont(font)
            # Bold new
            if focused_prop:
                label = self._property_labels.get(focused_prop)
                if label:
                    font = label.font()
                    font.setBold(True)
                    label.setFont(font)
            self._focused_prop = focused_prop

    def _create_single_property_widget(self, prop_type: PropType) -> QWidget:
        """Create input widget for a single-value property, with change signal."""
        name = prop_type.name
        ptype = prop_type.type

        if prop_type.enumeration:
            widget = ScrollSafeComboBox()
            for value in prop_type.enumeration:
                widget.addItem(str(value), value)
            widget.activated.connect(lambda _idx, n=name: self._on_widget_changed(n))
            return widget

        if ptype == "bool":
            widget = BoolValueWidget()
            widget.changed.connect(lambda n=name: self._on_bool_changed(n))
            return widget
        if ptype == "int":
            widget = ScrollSafeSpinBox()
            widget.setRange(-999999999, 999999999)
            widget.valueChanged.connect(lambda _val, n=name: self._on_widget_changed(n))
            return widget
        # float or str
        widget = QLineEdit()
        if ptype == "float":
            widget.setPlaceholderText(say("Enter a number"))
        widget.textEdited.connect(lambda _text, n=name: self._on_widget_changed(n))
        return widget

    def _on_widget_changed(self, name: str):
        """Handle user modification of a single property widget."""
        if self._loading:
            return
        self._user_modified.add(name)
        self._cleared.discard(name)
        self._update_prop_style(name)

    def _on_bool_changed(self, name: str):
        """Handle a click on a bool radio button.

        "Not set" is the absence of a value, not a third value, so picking it
        clears the property -- exactly what the Clear button does.
        """
        if self._loading:
            return
        if self._property_widgets[name].value() is None:
            self._on_clear_property(name)
        else:
            self._on_widget_changed(name)

    def _on_reset_property(self, name: str):
        """Handle Reset button click: restore initial value."""
        self._user_modified.discard(name)
        self._cleared.discard(name)

        prop_type = next(pt for pt in self.prop_types if pt.name == name)
        widget = self._property_widgets[name]
        initial = self._initial_widget_values.get(name)

        self._loading = True
        try:
            if prop_type.type == "bool":
                # initial is None when the video had no value: back to "not set"
                widget.set_value(initial)
            elif prop_type.enumeration:
                index = widget.findData(initial) if initial is not None else 0
                widget.setCurrentIndex(max(index, 0))
            elif prop_type.type == "int":
                widget.setValue(int(initial) if initial is not None else 0)
            elif prop_type.type == "float":
                widget.setText(str(initial) if initial is not None else "")
            else:
                widget.setText(str(initial) if initial is not None else "")
        finally:
            self._loading = False

        self._update_prop_style(name)

    def _on_clear_property(self, name: str):
        """Handle Clear button click: remove the property value."""
        self._cleared.add(name)
        self._user_modified.discard(name)

        # Reset widget to default value
        prop_type = next(pt for pt in self.prop_types if pt.name == name)
        default_values = prop_type.default
        default = default_values[0] if default_values else None
        widget = self._property_widgets[name]

        self._loading = True
        try:
            if prop_type.type == "bool":
                # Cleared means no value at all, which is what "not set" shows.
                widget.set_value(None)
            elif prop_type.enumeration:
                index = widget.findData(default) if default is not None else 0
                widget.setCurrentIndex(max(index, 0))
            elif prop_type.type == "int":
                widget.setValue(int(default) if default is not None else 0)
            elif prop_type.type == "float":
                widget.setText(str(default) if default is not None else "")
            else:
                widget.setText(str(default) if default else "")
        finally:
            self._loading = False

        self._update_prop_style(name)

    def _update_prop_style(self, name: str):
        """Update styling and button visibility for a single property."""
        widget = self._property_widgets.get(name)
        if not widget:
            return

        is_defined = self._initially_defined.get(name, False)
        is_cleared = name in self._cleared
        is_modified = name in self._user_modified

        # Italic when showing default value (not explicitly set)
        use_italic = is_cleared or (not is_defined and not is_modified)
        font = widget.font()
        font.setItalic(use_italic)
        widget.setFont(font)

        # Blue text when value differs from initial
        if is_modified:
            widget.setStyleSheet("color: #0055cc;")
        else:
            widget.setStyleSheet("")

        # Reset button visible when value differs from initial
        reset_btn = self._reset_buttons.get(name)
        if reset_btn:
            reset_btn.setVisible(is_modified or is_cleared)

        # Clear button visible when a value would be saved
        clear_btn = self._clear_buttons.get(name)
        if clear_btn:
            clear_btn.setVisible(not is_cleared and (is_defined or is_modified))

    def _read_widget_value(self, prop_type: PropType, widget: QWidget):
        """Read the current value from a property widget."""
        ptype = prop_type.type
        if prop_type.multiple:
            return widget.get_values()
        if ptype == "bool":
            return widget.value()  # None when "not set" is selected
        if prop_type.enumeration:
            return widget.currentData()
        if ptype == "int":
            return widget.value()
        if ptype == "float":
            text = widget.text().strip()
            default_values = prop_type.default
            default = default_values[0] if default_values else None
            return float(text) if text else default
        return widget.text()

    def _load_properties(self):
        """Load current property values into widgets."""
        self._initial_widget_values: dict = {}

        if not self.ctx.has_database():
            return

        video_properties = getattr(self.video, "properties", {}) or {}

        self._loading = True
        try:
            for prop_type in self.prop_types:
                name = prop_type.name
                widget = self._property_widgets.get(name)
                if not widget:
                    continue

                # Track if property is explicitly defined on this video
                prop_values = video_properties.get(name)
                is_defined = prop_values is not None and len(prop_values) > 0
                self._initially_defined[name] = is_defined

                # Get default value from default list
                default_values = prop_type.default
                default = default_values[0] if default_values else None

                # Get current value
                value = self.video.get_property(name, default)

                ptype = prop_type.type
                is_multiple = prop_type.multiple
                enumeration = prop_type.enumeration

                # Handle multiple values widget
                if is_multiple:
                    widget.set_values(value)
                    self._initial_widget_values[name] = self._read_widget_value(
                        prop_type, widget
                    )
                    continue

                # Handle enumeration combo box
                if enumeration:
                    if isinstance(value, (list, tuple)):
                        value = value[0] if value else enumeration[0]
                    index = widget.findData(value)
                    if index >= 0:
                        widget.setCurrentIndex(index)
                elif isinstance(value, (list, tuple)):
                    value = value[0] if value else None

                # Handle simple types
                if not enumeration:
                    if ptype == "bool":
                        # "Not set" whenever the video carries no value: for a
                        # bool the default would otherwise be indistinguishable
                        # from an explicit False.
                        widget.set_value(value if is_defined else None)
                    elif ptype == "int":
                        widget.setValue(int(value) if value is not None else 0)
                    elif ptype == "float":
                        widget.setText(str(value) if value is not None else "")
                    elif ptype == "str":
                        widget.setText(str(value) if value else "")
                    else:
                        widget.setText(str(value) if value else "")

                self._initial_widget_values[name] = self._read_widget_value(
                    prop_type, widget
                )
                self._update_prop_style(name)
        finally:
            self._loading = False

    def _on_accept(self):
        """Save changes and close dialog."""
        if not self.ctx.has_database():
            self.accept()
            return

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setEnabled(False)

        # {prop_name: [values]} to send to backend
        properties = {}

        for prop_type in self.prop_types:
            name = prop_type.name
            widget = self._property_widgets.get(name)
            if not widget:
                continue

            # Cleared single property: send empty list to delete
            if name in self._cleared:
                if self._initially_defined.get(name, False):
                    properties[name] = []
                continue

            try:
                new_value = self._read_widget_value(prop_type, widget)
                initial = self._initial_widget_values.get(name)
                if new_value != initial:
                    if isinstance(new_value, list):
                        properties[name] = new_value
                    else:
                        properties[name] = [new_value]
            except (ValueError, TypeError):
                pass

        if properties:
            self.ctx.set_video_properties(self.video.video_id, properties)

        self.accept()
