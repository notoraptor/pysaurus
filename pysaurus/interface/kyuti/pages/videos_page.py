"""
Videos page for browsing and managing videos.
"""

from html import escape

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QCursor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.classes import Selector
from pysaurus.core.constants import PYTHON_DEFAULT_SOURCES, VIDEO_DEFAULT_SORTING
from pysaurus.core.language import say
from pysaurus.dbview.field_stat import FieldStat
from pysaurus.interface.common.common import FIELD_MAP, Uniconst, format_group_value
from pysaurus.interface.kyuti.app_context import AppContext
from pysaurus.interface.kyuti.dialogs import (
    BatchEditPropertyDialog,
    GoToPageDialog,
    GroupingDialog,
    SortingDialog,
    SourcesDialog,
    VideoPropertiesDialog,
)
from pysaurus.interface.kyuti.dialogs.video_confirm_dialog import VideoConfirmDialog
from pysaurus.interface.kyuti.widgets.left_click_menu import LeftClickMenu
from pysaurus.interface.kyuti.widgets.video_list_item import VideoListItem
from pysaurus.properties.properties import PropType
from pysaurus.video.video_constants import SIMILARITY_FIELDS
from pysaurus.video.video_pattern import VideoPattern
from pysaurus.video.video_search_context import VideoSearchContext
from pysaurus.video.video_sorting import VideoSorting


class VideosPage(QWidget):
    """
    Main page for browsing videos.

    Layout:
    - Toolbar at top
    - Splitter with sidebar (filters) and content (video grid/list)
    - Pagination at bottom
    """

    # Signals for long operations that require a ProcessPage
    update_database_requested = Signal()
    find_similar_requested = Signal()
    find_similar_reencoded_requested = Signal()
    move_video_requested = Signal(int, str)  # video_id, directory
    status_message_requested = Signal(str, int)  # message, timeout

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.page_size = 20
        self.page_number = 0
        self._video_list_items: list[VideoListItem] = []
        self._videos: list[VideoPattern] = []  # Current videos for list view
        self._selected_video_id: int | None = None
        self._group_stats: list[FieldStat] = []
        self._current_group_index: int = -1
        self._selected_video_ids: set[int] = set()  # For multiple selection
        self._diff_fields: set[str] = set()  # Fields that differ in similarity group
        self._file_title_diffs: dict[int, list[tuple[int, int]]] = {}  # Character diffs
        self._grouped_by_moves: bool = False  # True when grouped by move_id
        self._grouped_by_similarity: bool = (
            False  # True when grouped by similarity field
        )
        self._similarity_field: str | None = None  # Current similarity field name
        self._total_pages: int = 1  # Total number of pages (for go to page dialog)
        self.confirm_not_found_deletion: bool = (
            True  # Confirm before deleting "not found" entries
        )
        self._classifier_path: list[str] = []  # Current classifier path
        self._is_classifying: bool = (
            False  # True when classifier is active (multiple property)
        )
        self._selector: Selector = Selector(False, set())  # Selection state
        self._known_view_generation: int = 0  # Last ViewContext.generation seen
        self._show_only_selected: bool = (
            False  # Toggle for showing only selected videos
        )
        self._view_count: int = 0  # Total videos in current view (for selector size)
        self._search_mode: str = "and"  # Current search mode
        self._active_search_text: str = ""  # Text of the currently active search
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main content with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Sidebar (filters)
        sidebar = self._create_sidebar()
        splitter.addWidget(sidebar)

        # Content area
        content = self._create_content_area()
        splitter.addWidget(content)

        # Set splitter proportions (compact sidebar)
        splitter.setSizes([150, 850])

        # Bottom bar with stats and pagination
        bottom_bar = self._create_bottom_bar()
        layout.addWidget(bottom_bar)

    def _setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Ctrl+G - Grouping
        shortcut_grouping = QShortcut(QKeySequence("Ctrl+G"), self)
        shortcut_grouping.activated.connect(self._on_set_grouping)

        # Ctrl+F - Search (focus on search input)
        shortcut_search = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_search.activated.connect(self._focus_search)

        # Ctrl+S - Sorting
        shortcut_sorting = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        shortcut_sorting.activated.connect(self._on_set_sorting)

        # Ctrl+T - Sources
        shortcut_sources = QShortcut(QKeySequence("Ctrl+T"), self)
        shortcut_sources.activated.connect(self._on_edit_sources)

        # Ctrl+O - Random video
        shortcut_random = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_random.activated.connect(self._on_random_video)

        # Ctrl+R - Refresh
        shortcut_refresh = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_refresh.activated.connect(self.refresh)

        # Left/Right - Page navigation
        shortcut_prev_page = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        shortcut_prev_page.activated.connect(self._go_prev)

        shortcut_next_page = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        shortcut_next_page.activated.connect(self._go_next)

        # Up/Down - Group navigation
        shortcut_prev_group = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        shortcut_prev_group.activated.connect(self._go_prev_group)

        shortcut_next_group = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        shortcut_next_group.activated.connect(self._go_next_group)

        # Ctrl+A - Select all (current page)
        shortcut_select_all = QShortcut(QKeySequence("Ctrl+A"), self)
        shortcut_select_all.activated.connect(self._select_all)

        # Ctrl+Shift+A - Select all in view
        shortcut_select_all_view = QShortcut(QKeySequence("Ctrl+Shift+A"), self)
        shortcut_select_all_view.activated.connect(self._select_all_in_view)

        # Escape - Clear selection
        shortcut_escape = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        shortcut_escape.activated.connect(self._clear_selection)

        # Ctrl+Shift+D - Toggle show only selected
        shortcut_show_selected = QShortcut(QKeySequence("Ctrl+Shift+D"), self)
        shortcut_show_selected.activated.connect(self._toggle_show_only_selected)

        # Enter - Open selected video
        shortcut_enter = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        shortcut_enter.activated.connect(self._open_selected)

        # Delete - Delete selected
        shortcut_delete = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        shortcut_delete.activated.connect(self._delete_selected)

        # Ctrl+L - Play list
        shortcut_playlist = QShortcut(QKeySequence("Ctrl+L"), self)
        shortcut_playlist.activated.connect(self._on_playlist)

        # Home/End - First/Last page
        shortcut_home = QShortcut(QKeySequence(Qt.Key.Key_Home), self)
        shortcut_home.activated.connect(self._go_first)

        shortcut_end = QShortcut(QKeySequence(Qt.Key.Key_End), self)
        shortcut_end.activated.connect(self._go_last)

        # Ctrl+E - Sources (advanced/expression)
        shortcut_expression = QShortcut(QKeySequence("Ctrl+E"), self)
        shortcut_expression.activated.connect(self._on_edit_source_expression)

        # Ctrl+Shift+T - Reset sources
        shortcut_reset_sources = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        shortcut_reset_sources.activated.connect(self._clear_sources)

        # Ctrl+Shift+G - Reset grouping
        shortcut_reset_grouping = QShortcut(QKeySequence("Ctrl+Shift+G"), self)
        shortcut_reset_grouping.activated.connect(self._clear_grouping)

        # Ctrl+Shift+F - Reset search
        shortcut_reset_search = QShortcut(QKeySequence("Ctrl+Shift+F"), self)
        shortcut_reset_search.activated.connect(self._clear_search)

        # Ctrl+P - Manage properties
        shortcut_properties = QShortcut(QKeySequence("Ctrl+P"), self)
        shortcut_properties.activated.connect(self._go_to_properties)

    def _focus_search(self):
        """Focus the search input."""
        self.search_input.setFocus()
        self.search_input.selectAll()

    def _select_all(self):
        """Select all videos on the current page."""
        for v in self._videos:
            self._selector.include(v.video_id)
        self._selected_video_ids = {v.video_id for v in self._videos}
        self._update_selection_display()

    def _select_all_in_view(self):
        """Select all videos in the current filtered view (not just current page)."""
        self._selector.select_all()
        # Update local set for current page display
        self._selected_video_ids = {v.video_id for v in self._videos}
        self._update_selection_display()

    def _toggle_show_only_selected(self, checked: bool = None):
        """Toggle between showing all videos and showing only selected."""
        if checked is None:
            checked = not self._show_only_selected
        self._show_only_selected = checked
        self.page_number = 0
        self.refresh()

    def _on_selection_menu(self):
        """Show context menu with selection actions."""
        count = self._selector.size_from(self._view_count)
        has_selection = count > 0

        menu = LeftClickMenu(self)
        action_show = menu.addAction(say("Show Only Selected") + "\tCtrl+Shift+D")
        action_show.setCheckable(True)
        action_show.setChecked(self._show_only_selected)
        action_show.setEnabled(has_selection or self._show_only_selected)
        action_show.triggered.connect(self._toggle_show_only_selected)
        menu.addSeparator()
        action_toggle = menu.addAction(say("Toggle Watched"))
        action_toggle.setEnabled(has_selection)
        action_toggle.triggered.connect(self._on_toggle_watched_selection)

        # Edit Properties as a submenu listing each property
        edit_submenu = menu.addMenu(say("Edit Properties"))
        edit_submenu.setEnabled(has_selection)
        if has_selection and self.ctx.has_database():
            prop_types = self.ctx.get_prop_types()
            if prop_types:
                for prop_type in prop_types:
                    action = edit_submenu.addAction(prop_type.name)
                    action.setData(prop_type)
                edit_submenu.triggered.connect(
                    lambda a: self._edit_property_for_selection(a.data())
                )
            else:
                no_props = edit_submenu.addAction(say("(no properties defined)"))
                no_props.setEnabled(False)

        menu.exec(
            self.btn_selection_settings.mapToGlobal(
                self.btn_selection_settings.rect().bottomLeft()
            )
        )

    def _clear_selection(self):
        """Clear video selection."""
        self._selector.deselect_all()
        self._selected_video_ids.clear()
        self._selected_video_id = None
        # Reset show only selected if active
        if self._show_only_selected:
            self._show_only_selected = False
        self._update_selection_display()

    def _purge_video_from_selection(self, video_id: int):
        """Drop a deleted video's ID from the selector (avoids a stale ghost entry)."""
        self._selector.exclude(video_id)
        self._update_selection_display()

    def _update_selection_display(self):
        """Update the visual display of selected videos."""
        # Update selection from selector for current page
        self._selected_video_ids = {
            v.video_id for v in self._videos if self._selector.contains(v.video_id)
        }

        for item in self._video_list_items:
            item.selected = self._selector.contains(item.video.video_id)

        # Update selection indicator and batch action buttons
        # Use selector size for total selection count
        count = self._selector.size_from(self._view_count)
        has_selection = count > 0
        if has_selection:
            self.selection_label.setText(say("{count} selected", count=count))
            self.selection_label.setStyleSheet(
                "color: #0078d4; font-weight: bold; background: transparent;"
            )
        else:
            self.selection_label.setText(say("no selection"))
            self.selection_label.setStyleSheet(
                "color: #0078d4; font-style: italic; background: transparent;"
            )
        self.btn_selection_clear.setEnabled(has_selection)

    def _open_selected(self):
        """Open the selected video(s)."""
        # Don't open video if focus is on search input (let Enter trigger search instead)
        if self.search_input.hasFocus():
            self._on_search()
            return
        video_id = self._selected_video_id
        if not video_id and self._selected_video_ids:
            video_id = next(iter(self._selected_video_ids))
        if video_id and self.ctx.has_database():
            self._open_video(video_id)

    def _delete_selected(self):
        """Delete the selected video(s) from the database."""
        if not self._selected_video_ids and not self._selected_video_id:
            return

        video_ids = self._selected_video_ids or {self._selected_video_id}
        count = len(video_ids)

        reply = QMessageBox.question(
            self,
            say("Delete Videos"),
            say(
                "Delete {count} video(s) from the database?\n\n"
                "(Files will NOT be deleted from disk)",
                count=count,
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.ctx.has_database():
                self.ctx.delete_video_entries(video_ids)
                self.status_message_requested.emit(
                    say("{count} video(s) removed from database", count=count), 5000
                )
                self._clear_selection()

    def _on_playlist(self):
        """Generate and open a playlist of the current view."""
        if not self.ctx.has_database():
            return

        try:
            # Call the playlist method from the API
            filename = self.ctx.playlist()

            # Emit signal for status message
            self.status_message_requested.emit(
                say("Playlist opened: {filename}", filename=filename), 5000
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                say("Error Creating Playlist"),
                say("Failed to create playlist: {error}", error=e),
            )

    def _create_filter_section(self, color: str) -> QFrame:
        """Create a filter section frame with alternating background color."""
        section = QFrame()
        section.setStyleSheet(
            f"QFrame {{ background-color: {color}; border-radius: 3px; }}"
        )
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(4, 4, 4, 8)  # Extra padding at bottom
        section_layout.setSpacing(2)
        return section, section_layout

    def _create_sidebar(self) -> QWidget:
        """Create the sidebar with filters."""
        # Alternating colors for sections
        color_light = "#f0f0f0"
        color_lighter = "#ffffff"

        sidebar = QFrame()
        sidebar.setFrameStyle(QFrame.Shape.StyledPanel)
        sidebar.setMaximumWidth(200)
        # Compact button style for sidebar (font size set via QFont below)
        sidebar.setStyleSheet("""
            QPushButton {
                padding: 2px 6px;
            }
            QPushButton#clearBtn {
                background-color: #cc3333;
                color: white;
                font-weight: bold;
                padding: 2px 4px;
            }
            QPushButton#clearBtn:hover {
                background-color: #dd4444;
            }
            QPushButton#clearBtn:disabled {
                background-color: #cccccc;
                color: #888888;
            }
            QPushButton#settingsBtn {
                background-color: #1976d2;
                color: white;
                font-weight: bold;
                padding: 2px 4px;
            }
            QPushButton#settingsBtn:hover {
                background-color: #1565c0;
            }
            QPushButton#classifierBtn {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 2px 4px;
            }
            QPushButton#classifierBtn:hover {
                background-color: #45a049;
            }
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)

        # Sources section
        sources_section, sources_layout = self._create_filter_section(color_light)
        sources_header = QHBoxLayout()
        sources_header.setSpacing(2)
        self._sources_label = QLabel(say("Sources"))
        self._sources_label.setStyleSheet("font-weight: bold; background: transparent;")
        sources_header.addWidget(self._sources_label)
        sources_header.addStretch()
        self.btn_sources = QPushButton("⚙")
        self.btn_sources.setObjectName("settingsBtn")
        self.btn_sources.setToolTip(say("Edit video sources (Ctrl+T)"))
        self.btn_sources.setFixedWidth(28)
        self.btn_sources.clicked.connect(self._on_edit_sources)
        sources_header.addWidget(self.btn_sources)
        self.btn_sources_clear = QPushButton("✕")
        self.btn_sources_clear.setObjectName("clearBtn")
        self.btn_sources_clear.setToolTip(
            say("Reset to default sources (Ctrl+Shift+T)")
        )
        self.btn_sources_clear.setFixedWidth(28)
        self.btn_sources_clear.clicked.connect(self._clear_sources)
        sources_header.addWidget(self.btn_sources_clear)
        sources_layout.addLayout(sources_header)

        self.sources_info = QLabel(say("All readable"))
        self.sources_info.setStyleSheet("color: #555; background: transparent;")
        self.sources_info.setWordWrap(True)
        self.sources_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sources_layout.addWidget(self.sources_info)
        layout.addWidget(sources_section)

        # Grouping section
        grouping_section, grouping_layout = self._create_filter_section(color_lighter)
        grouping_header = QHBoxLayout()
        grouping_header.setSpacing(2)
        self._grouping_label = QLabel(say("Grouping"))
        self._grouping_label.setStyleSheet(
            "font-weight: bold; background: transparent;"
        )
        grouping_header.addWidget(self._grouping_label)
        grouping_header.addStretch()
        self.btn_grouping = QPushButton("⚙")
        self.btn_grouping.setObjectName("settingsBtn")
        self.btn_grouping.setToolTip(say("Configure video grouping (Ctrl+G)"))
        self.btn_grouping.setFixedWidth(28)
        self.btn_grouping.clicked.connect(self._on_set_grouping)
        grouping_header.addWidget(self.btn_grouping)
        self.btn_grouping_clear = QPushButton("✕")
        self.btn_grouping_clear.setObjectName("clearBtn")
        self.btn_grouping_clear.setToolTip(say("Remove grouping (Ctrl+Shift+G)"))
        self.btn_grouping_clear.setFixedWidth(28)
        self.btn_grouping_clear.clicked.connect(self._clear_grouping)
        grouping_header.addWidget(self.btn_grouping_clear)
        grouping_layout.addLayout(grouping_header)

        self.grouping_info = QLabel(say("No grouping"))
        self.grouping_info.setStyleSheet("color: #555; background: transparent;")
        self.grouping_info.setWordWrap(True)
        self.grouping_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grouping_layout.addWidget(self.grouping_info)

        # Button for confirming all unique moves (only visible when grouped by move_id)
        self.btn_confirm_unique_moves = QPushButton(say("Confirm all unique moves"))
        self.btn_confirm_unique_moves.setToolTip(
            say("Automatically confirm all moves with a single destination")
        )
        self.btn_confirm_unique_moves.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self.btn_confirm_unique_moves.clicked.connect(self._on_confirm_unique_moves)
        self.btn_confirm_unique_moves.setVisible(False)
        grouping_layout.addWidget(self.btn_confirm_unique_moves)

        layout.addWidget(grouping_section)

        # Classifier Path section (hidden by default, shown when path is active)
        self.classifier_section, classifier_layout = self._create_filter_section(
            color_light
        )
        self._classifier_label = QLabel(say("Classifier Path"))
        self._classifier_label.setStyleSheet(
            "font-weight: bold; background: transparent;"
        )
        self._classifier_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        classifier_layout.addWidget(self._classifier_label)

        # Path display area (vertical list of path values)
        self.classifier_path_widget = QWidget()
        self.classifier_path_widget.setStyleSheet("background: transparent;")
        self.classifier_path_layout = QVBoxLayout(self.classifier_path_widget)
        self.classifier_path_layout.setContentsMargins(0, 0, 0, 0)
        self.classifier_path_layout.setSpacing(2)
        classifier_layout.addWidget(self.classifier_path_widget)

        # Classifier action buttons
        classifier_btn_layout = QHBoxLayout()
        classifier_btn_layout.setSpacing(2)

        self.btn_classifier_reverse = QPushButton(say("Reverse"))
        self.btn_classifier_reverse.setToolTip(say("Reverse the order of path values"))
        self.btn_classifier_reverse.clicked.connect(self._on_classifier_reverse)
        classifier_btn_layout.addWidget(self.btn_classifier_reverse)

        self.btn_classifier_concat = QPushButton(say("Concat..."))
        self.btn_classifier_concat.setToolTip(
            say("Concatenate path values into a string property")
        )
        self.btn_classifier_concat.clicked.connect(self._on_classifier_concatenate)
        classifier_btn_layout.addWidget(self.btn_classifier_concat)

        classifier_layout.addLayout(classifier_btn_layout)

        self.classifier_section.setVisible(False)
        layout.addWidget(self.classifier_section)

        # Search section
        search_section, search_layout = self._create_filter_section(color_light)
        search_header = QHBoxLayout()
        search_header.setSpacing(2)
        self._search_label = QLabel(say("Search"))
        self._search_label.setStyleSheet("font-weight: bold; background: transparent;")
        search_header.addWidget(self._search_label)
        search_header.addStretch()
        self.btn_search_clear = QPushButton("✕")
        self.btn_search_clear.setObjectName("clearBtn")
        self.btn_search_clear.setToolTip(say("Clear search (Ctrl+Shift+F)"))
        self.btn_search_clear.setFixedWidth(28)
        self.btn_search_clear.clicked.connect(self._clear_search)
        search_header.addWidget(self.btn_search_clear)
        search_layout.addLayout(search_header)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(say("Search... (Ctrl+F)"))
        self.search_input.setToolTip(say("Search videos (Ctrl+F)"))
        self.search_input.returnPressed.connect(self._on_search)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_input)

        # First row: AND, OR buttons
        search_btn_layout1 = QHBoxLayout()
        search_btn_layout1.setSpacing(2)
        self.btn_search_and = QPushButton(say("AND"))
        self.btn_search_and.setToolTip(say("Search for all terms"))
        self.btn_search_and.clicked.connect(self._on_search_and)
        search_btn_layout1.addWidget(self.btn_search_and)

        self.btn_search_or = QPushButton(say("OR"))
        self.btn_search_or.setToolTip(say("Search for any term"))
        self.btn_search_or.clicked.connect(self._on_search_or)
        search_btn_layout1.addWidget(self.btn_search_or)
        search_layout.addLayout(search_btn_layout1)

        # Second row: Exact, ID, Clear buttons
        search_btn_layout2 = QHBoxLayout()
        search_btn_layout2.setSpacing(2)
        self.btn_search_exact = QPushButton(say("Exact"))
        self.btn_search_exact.setToolTip(say("Search for exact sentence"))
        self.btn_search_exact.clicked.connect(self._on_search_exact)
        search_btn_layout2.addWidget(self.btn_search_exact)

        self.btn_search_id = QPushButton(say("ID"))
        self.btn_search_id.setToolTip(say("Search by video ID"))
        self.btn_search_id.clicked.connect(self._on_search_id)
        search_btn_layout2.addWidget(self.btn_search_id)
        search_layout.addLayout(search_btn_layout2)
        layout.addWidget(search_section)

        # Sorting section
        sorting_section, sorting_layout = self._create_filter_section(color_lighter)
        sorting_header = QHBoxLayout()
        sorting_header.setSpacing(2)
        self._sorting_label = QLabel(say("Sorting"))
        self._sorting_label.setStyleSheet("font-weight: bold; background: transparent;")
        sorting_header.addWidget(self._sorting_label)
        sorting_header.addStretch()
        self.btn_sorting = QPushButton("⚙")
        self.btn_sorting.setObjectName("settingsBtn")
        self.btn_sorting.setToolTip(say("Configure video sorting (Ctrl+Shift+S)"))
        self.btn_sorting.setFixedWidth(28)
        self.btn_sorting.clicked.connect(self._on_set_sorting)
        sorting_header.addWidget(self.btn_sorting)
        self.btn_sorting_clear = QPushButton("✕")
        self.btn_sorting_clear.setObjectName("clearBtn")
        self.btn_sorting_clear.setToolTip(say("Reset to default sorting"))
        self.btn_sorting_clear.setFixedWidth(28)
        self.btn_sorting_clear.clicked.connect(self._clear_sorting)
        sorting_header.addWidget(self.btn_sorting_clear)
        sorting_layout.addLayout(sorting_header)

        self.sorting_info = QLabel(say("Date") + " ▼")
        self.sorting_info.setStyleSheet("color: #555; background: transparent;")
        self.sorting_info.setWordWrap(True)
        self.sorting_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sorting_layout.addWidget(self.sorting_info)
        layout.addWidget(sorting_section)

        # Selection section
        selection_section, selection_layout = self._create_filter_section(color_light)
        selection_header = QHBoxLayout()
        selection_header.setSpacing(2)
        self._selection_header_label = QLabel(say("Selection"))
        self._selection_header_label.setStyleSheet(
            "font-weight: bold; background: transparent;"
        )
        selection_header.addWidget(self._selection_header_label)
        selection_header.addStretch()
        self.btn_selection_settings = QPushButton("⚙")
        self.btn_selection_settings.setObjectName("settingsBtn")
        self.btn_selection_settings.setToolTip(say("Selection actions"))
        self.btn_selection_settings.setFixedWidth(28)
        self.btn_selection_settings.clicked.connect(self._on_selection_menu)
        selection_header.addWidget(self.btn_selection_settings)
        self.btn_selection_clear = QPushButton("✕")
        self.btn_selection_clear.setObjectName("clearBtn")
        self.btn_selection_clear.setToolTip(say("Clear selection (Escape)"))
        self.btn_selection_clear.setFixedWidth(28)
        self.btn_selection_clear.setEnabled(False)
        self.btn_selection_clear.clicked.connect(self._clear_selection)
        selection_header.addWidget(self.btn_selection_clear)
        selection_layout.addLayout(selection_header)

        # Selection info label + Page/All buttons
        selection_row = QHBoxLayout()
        selection_row.setSpacing(2)
        self.selection_label = QLabel(say("no selection"))
        self.selection_label.setStyleSheet(
            "color: #0078d4; font-style: italic; background: transparent;"
        )
        selection_row.addWidget(self.selection_label, 1)
        self.btn_select_page = QPushButton(say("Page"))
        self.btn_select_page.setToolTip(
            say("Select all videos on current page (Ctrl+A)")
        )
        self.btn_select_page.clicked.connect(self._select_all)
        selection_row.addWidget(self.btn_select_page)
        self.btn_select_all = QPushButton(say("All"))
        self.btn_select_all.setToolTip(
            say("Select all videos in current view (Ctrl+Shift+A)")
        )
        self.btn_select_all.clicked.connect(self._select_all_in_view)
        selection_row.addWidget(self.btn_select_all)
        selection_layout.addLayout(selection_row)
        layout.addWidget(selection_section)

        # Groups panel (visible only when grouping is active)
        self.groups_panel = QWidget()
        groups_panel_layout = QVBoxLayout(self.groups_panel)
        groups_panel_layout.setContentsMargins(4, 4, 4, 0)
        groups_panel_layout.setSpacing(2)

        # Title with classifier button
        groups_header = QHBoxLayout()
        groups_header.setSpacing(2)
        self._groups_title = QLabel(say("Groups"))
        self._groups_title.setStyleSheet("font-weight: bold; background: transparent;")
        groups_header.addWidget(self._groups_title)
        groups_header.addStretch()

        self.btn_add_to_classifier = QPushButton("✙")
        self.btn_add_to_classifier.setObjectName("classifierBtn")
        self.btn_add_to_classifier.setFixedWidth(28)
        self.btn_add_to_classifier.setToolTip(
            say("Add current group to classifier path")
        )
        self.btn_add_to_classifier.clicked.connect(self._on_classifier_add_group)
        self.btn_add_to_classifier.setVisible(False)
        groups_header.addWidget(self.btn_add_to_classifier)

        groups_panel_layout.addLayout(groups_header)

        # Navigation: << < X/Y > >>
        nav_btn_style = (
            "QPushButton { font-weight: bold; }"
            "QPushButton:hover { background-color: #1976d2; color: white; }"
        )
        groups_nav = QHBoxLayout()
        groups_nav.setContentsMargins(0, 0, 0, 0)
        groups_nav.setSpacing(2)

        self.btn_first_group = QPushButton("<<")
        self.btn_first_group.setFixedWidth(28)
        self.btn_first_group.setToolTip(say("First group"))
        self.btn_first_group.setStyleSheet(nav_btn_style)
        self.btn_first_group.clicked.connect(self._go_first_group)
        groups_nav.addWidget(self.btn_first_group)

        self.btn_prev_group = QPushButton("<")
        self.btn_prev_group.setFixedWidth(28)
        self.btn_prev_group.setToolTip(say("Previous group (Up arrow)"))
        self.btn_prev_group.setStyleSheet(nav_btn_style)
        self.btn_prev_group.clicked.connect(self._go_prev_group)
        groups_nav.addWidget(self.btn_prev_group)

        self.group_count_label = QLabel("0/0")
        self.group_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        groups_nav.addWidget(self.group_count_label, 1)

        self.btn_next_group = QPushButton(">")
        self.btn_next_group.setFixedWidth(28)
        self.btn_next_group.setToolTip(say("Next group (Down arrow)"))
        self.btn_next_group.setStyleSheet(nav_btn_style)
        self.btn_next_group.clicked.connect(self._go_next_group)
        groups_nav.addWidget(self.btn_next_group)

        self.btn_last_group = QPushButton(">>")
        self.btn_last_group.setFixedWidth(28)
        self.btn_last_group.setToolTip(say("Last group"))
        self.btn_last_group.setStyleSheet(nav_btn_style)
        self.btn_last_group.clicked.connect(self._go_last_group)
        groups_nav.addWidget(self.btn_last_group)

        groups_panel_layout.addLayout(groups_nav)

        self.groups_list = QListWidget()
        self.groups_list.setAlternatingRowColors(True)
        self.groups_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.groups_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.groups_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.groups_list.setStyleSheet("QListWidget::item:selected { color: white; }")
        self.groups_list.currentRowChanged.connect(self._on_group_list_selected)
        groups_panel_layout.addWidget(self.groups_list)

        self.groups_panel.setVisible(False)
        layout.addWidget(self.groups_panel, 1)

        self._sidebar_stretch = layout.addStretch()
        self._sidebar_layout = layout

        # Apply reduced font size to all buttons in sidebar
        for btn in sidebar.findChildren(QPushButton):
            font = btn.font()
            font.setPointSizeF(font.pointSizeF() * 0.8)
            btn.setFont(font)

        # Let a click anywhere in the sidebar - including labels and section
        # backgrounds, which don't accept focus by default - take focus away
        # from whatever currently has it (e.g. search_input), instead of
        # being a no-op because the clicked widget never takes focus itself.
        # Buttons/list widgets already have their own (non-NoFocus) policy
        # and are left untouched.
        sidebar.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        for widget in sidebar.findChildren(QWidget):
            if widget.focusPolicy() == Qt.FocusPolicy.NoFocus:
                widget.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        return sidebar

    def _create_content_area(self) -> QWidget:
        """Create the main content area for videos."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # QListWidget hosts VideoListItem widgets via setItemWidget(). It
        # manages its own scroll natively; mutations via setItemWidget /
        # takeItem preserve the scroll position (no clear+rebuild during
        # state_changed).
        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.list_widget.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        # Don't auto-scroll to make the clicked/current item fully visible —
        # that's jarring when right-clicking a partially-visible item.
        self.list_widget.setAutoScroll(False)
        self.list_widget.setSpacing(2)
        self.list_widget.setContentsMargins(3, 0, 3, 3)
        # Transparent stylesheet so VideoListItem widgets paint their own background
        self.list_widget.setStyleSheet(
            "QListWidget { background: transparent; border: none; }"
            "QListWidget::item { background: transparent; }"
        )
        # Without this, Qt sets singleStep based on item height, so the wheel
        # jumps a full item per notch (one viewport-worth for tall items).
        self.list_widget.verticalScrollBar().setSingleStep(20)
        layout.addWidget(self.list_widget)

        # Stats bar (at bottom)
        self.stats_label = QLabel(
            say(
                "{count} videos | {size} | {duration}",
                count=0,
                size="0 B",
                duration="0:00:00",
            )
        )
        self.stats_label.setStyleSheet("font-size: 12px; padding: 5px;")
        layout.addWidget(self.stats_label)

        return content

    def _create_bottom_bar(self) -> QWidget:
        """Create the bottom bar with pagination."""
        bar = QFrame()
        bar.setFrameStyle(QFrame.Shape.StyledPanel)
        bar.setMaximumHeight(36)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        layout.addStretch()

        # Pagination controls
        self.btn_first = QPushButton("<<")
        self.btn_first.setFixedSize(32, 24)
        self.btn_first.setToolTip(say("First page (Home)"))
        self.btn_first.clicked.connect(self._go_first)
        layout.addWidget(self.btn_first)

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedSize(32, 24)
        self.btn_prev.setToolTip(say("Previous page (Left arrow)"))
        self.btn_prev.clicked.connect(self._go_prev)
        layout.addWidget(self.btn_prev)

        # Page indicator button (clickable to go to a specific page)
        self.page_button = QPushButton(
            say("Page {current}/{total}", current=1, total=1)
        )
        self.page_button.setMinimumWidth(80)
        self.page_button.setToolTip(say("Click to go to a specific page"))
        self.page_button.setFlat(True)
        self.page_button.setStyleSheet(
            "QPushButton { text-decoration: underline; color: #0078d4; }"
            "QPushButton:hover { color: #005a9e; }"
        )
        self.page_button.clicked.connect(self._on_go_to_page)
        layout.addWidget(self.page_button)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedSize(32, 24)
        self.btn_next.setToolTip(say("Next page (Right arrow)"))
        self.btn_next.clicked.connect(self._go_next)
        layout.addWidget(self.btn_next)

        self.btn_last = QPushButton(">>")
        self.btn_last.setFixedSize(32, 24)
        self.btn_last.setToolTip(say("Last page (End)"))
        self.btn_last.clicked.connect(self._go_last)
        layout.addWidget(self.btn_last)

        layout.addStretch()
        return bar

    def retranslateUi(self):
        """Re-apply the text of every *static* piece of chrome in the current
        language. Triggered by QEvent.LanguageChange (see changeEvent).

        The construction keeps its say() calls (the text stays readable at the
        call site), so this only *repeats* them for the persistent sidebar
        section headers, the fixed filter/pagination buttons and their
        tooltips; it is deliberately NOT called at startup. Dynamic content
        (video list, selection count, sources/grouping/sorting info, page
        indicator, stats, groups list) is retranslated on its own by refresh()
        via the state_changed signal.
        """
        # Sources section
        self._sources_label.setText(say("Sources"))
        self.btn_sources.setToolTip(say("Edit video sources (Ctrl+T)"))
        self.btn_sources_clear.setToolTip(
            say("Reset to default sources (Ctrl+Shift+T)")
        )
        # Grouping section
        self._grouping_label.setText(say("Grouping"))
        self.btn_grouping.setToolTip(say("Configure video grouping (Ctrl+G)"))
        self.btn_grouping_clear.setToolTip(say("Remove grouping (Ctrl+Shift+G)"))
        self.btn_confirm_unique_moves.setText(say("Confirm all unique moves"))
        self.btn_confirm_unique_moves.setToolTip(
            say("Automatically confirm all moves with a single destination")
        )
        # Classifier Path section
        self._classifier_label.setText(say("Classifier Path"))
        self.btn_classifier_reverse.setText(say("Reverse"))
        self.btn_classifier_reverse.setToolTip(say("Reverse the order of path values"))
        self.btn_classifier_concat.setText(say("Concat..."))
        self.btn_classifier_concat.setToolTip(
            say("Concatenate path values into a string property")
        )
        # Search section
        self._search_label.setText(say("Search"))
        self.btn_search_clear.setToolTip(say("Clear search (Ctrl+Shift+F)"))
        self.search_input.setPlaceholderText(say("Search... (Ctrl+F)"))
        self.search_input.setToolTip(say("Search videos (Ctrl+F)"))
        self.btn_search_and.setText(say("AND"))
        self.btn_search_and.setToolTip(say("Search for all terms"))
        self.btn_search_or.setText(say("OR"))
        self.btn_search_or.setToolTip(say("Search for any term"))
        self.btn_search_exact.setText(say("Exact"))
        self.btn_search_exact.setToolTip(say("Search for exact sentence"))
        self.btn_search_id.setText(say("ID"))
        self.btn_search_id.setToolTip(say("Search by video ID"))
        # Sorting section
        self._sorting_label.setText(say("Sorting"))
        self.btn_sorting.setToolTip(say("Configure video sorting (Ctrl+Shift+S)"))
        self.btn_sorting_clear.setToolTip(say("Reset to default sorting"))
        # Selection section
        self._selection_header_label.setText(say("Selection"))
        self.btn_selection_settings.setToolTip(say("Selection actions"))
        self.btn_selection_clear.setToolTip(say("Clear selection (Escape)"))
        self.btn_select_page.setText(say("Page"))
        self.btn_select_page.setToolTip(
            say("Select all videos on current page (Ctrl+A)")
        )
        self.btn_select_all.setText(say("All"))
        self.btn_select_all.setToolTip(
            say("Select all videos in current view (Ctrl+Shift+A)")
        )
        # Groups panel
        self._groups_title.setText(say("Groups"))
        self.btn_add_to_classifier.setToolTip(
            say("Add current group to classifier path")
        )
        self.btn_first_group.setToolTip(say("First group"))
        self.btn_prev_group.setToolTip(say("Previous group (Up arrow)"))
        self.btn_next_group.setToolTip(say("Next group (Down arrow)"))
        self.btn_last_group.setToolTip(say("Last group"))
        # Pagination bar
        self.btn_first.setToolTip(say("First page (Home)"))
        self.btn_prev.setToolTip(say("Previous page (Left arrow)"))
        self.page_button.setToolTip(say("Click to go to a specific page"))
        self.btn_next.setToolTip(say("Next page (Right arrow)"))
        self.btn_last.setToolTip(say("Last page (End)"))

    def changeEvent(self, event):
        """Qt posts LanguageChange to every widget when a QTranslator is
        installed or removed. That is our cue to re-pull the static chrome."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def refresh(self):
        """Refresh the video list."""
        if not self.ctx.has_database():
            return

        # A filter change (sources/search/grouping/group/classifier) since the
        # last refresh invalidates any active selection - it may no longer
        # refer to the same videos. Sorting alone does not bump the generation.
        if self.ctx.get_view_generation() != self._known_view_generation:
            self._clear_selection()

        # Pass selector to backend if showing only selected
        selector = self._selector if self._show_only_selected else None

        # Get videos from provider
        context: VideoSearchContext = self.ctx.get_videos(
            self.page_size, self.page_number, selector
        )

        # Store view count for selector size calculation
        self._view_count = context.view_count

        # Update stats
        self.stats_label.setText(
            say(
                "{count} videos | {size} | {duration}",
                count=context.view_count,
                size=context.selection_file_size,
                duration=context.selection_duration,
            )
        )

        # Sync page_number from clamped result (safety net)
        self.page_number = context.page_number

        # Update pagination
        nb_pages = max(1, context.nb_pages)
        self._total_pages = nb_pages
        self.page_button.setText(
            say("Page {current}/{total}", current=self.page_number + 1, total=nb_pages)
        )

        # Update pagination button states
        self.btn_first.setEnabled(self.page_number > 0)
        self.btn_prev.setEnabled(self.page_number > 0)
        self.btn_next.setEnabled(self.page_number < nb_pages - 1)
        self.btn_last.setEnabled(self.page_number < nb_pages - 1)

        # Selection buttons: "Page" only differs from "All" across several pages,
        # so hide it on a single page; hide both when the view is empty.
        self.btn_select_page.setVisible(nb_pages > 1)
        self.btn_select_all.setVisible(self._view_count > 0)

        # Update sources display
        self._update_sources_display(context.sources)

        # Update sorting display
        self._update_sorting_display(context.sorting)

        # Update search display
        self._update_search_display(context.search)

        # Update grouping info and group navigation
        if context.grouping:
            self._update_grouping_display(context)
            self._update_group_bar(context)

            # If grouping is active but no group is selected, select the first one
            if context.group_id is None and context.classifier_stats:
                self.ctx.set_group(0)
                # Re-fetch videos with the selected group
                context = self.ctx.get_videos(self.page_size, self.page_number)
                self._current_group_index = 0

            # Extract differing fields from common_fields (for similarity groups)
            self._diff_fields = {
                field
                for field, is_common in context.common_fields.items()
                if not is_common
            }
            # Extract file title character-level diffs
            self._file_title_diffs = context.file_title_diffs or {}

            # Update classifier path display
            self._update_classifier_path(context)
        else:
            self._diff_fields = set()
            self._file_title_diffs = {}
            self.grouping_info.setText(say("No grouping"))
            self.btn_grouping_clear.setEnabled(False)
            self._hide_groups_panel()
            self._group_stats = []
            self._current_group_index = -1
            self._grouped_by_moves = False
            self._grouped_by_similarity = False
            self._similarity_field = None
            self.btn_confirm_unique_moves.setVisible(False)
            # Hide classifier when no grouping
            self._classifier_path = []
            self._is_classifying = False
            self.classifier_section.setVisible(False)

        # Display videos
        self._display_videos(context.result)

        # Record the generation as of this refresh (after any internal
        # mutation above, e.g. auto-selecting the first group) so the next
        # refresh only clears the selection on a genuinely new filter change.
        self._known_view_generation = self.ctx.get_view_generation()

    def _update_group_bar(self, context: VideoSearchContext):
        """Update the groups panel in the sidebar."""
        self._group_stats = context.classifier_stats or []

        if not self._group_stats:
            self._hide_groups_panel()
            self._current_group_index = -1
            return

        # Show groups panel
        self._show_groups_panel()

        # Get current group index (group_id is the index)
        if context.group_id is not None and 0 <= context.group_id < len(
            self._group_stats
        ):
            self._current_group_index = context.group_id
        else:
            self._current_group_index = 0 if self._group_stats else -1

        # Populate groups list (block signals during update)
        self.groups_list.blockSignals(True)
        self.groups_list.clear()
        group_field = context.grouping.field if context.grouping else ""
        for stat in self._group_stats:
            value_str = format_group_value(group_field, stat.value)
            self.groups_list.addItem(f"{value_str} ({stat.count})")
        if self._current_group_index >= 0:
            self.groups_list.setCurrentRow(self._current_group_index)
        self.groups_list.blockSignals(False)

        # Update count label in sidebar panel header
        total_groups = len(self._group_stats)
        current_num = (
            self._current_group_index + 1 if self._current_group_index >= 0 else 0
        )
        self.group_count_label.setText(f"{current_num}/{total_groups}")

        # Update navigation button states
        self.btn_first_group.setEnabled(self._current_group_index > 0)
        self.btn_prev_group.setEnabled(self._current_group_index > 0)
        self.btn_next_group.setEnabled(
            self._current_group_index >= 0
            and self._current_group_index < total_groups - 1
        )
        self.btn_last_group.setEnabled(
            self._current_group_index >= 0
            and self._current_group_index < total_groups - 1
        )

    def _show_groups_panel(self):
        """Show the groups panel and remove the sidebar stretch."""
        if not self.groups_panel.isVisible():
            self._sidebar_layout.removeItem(
                self._sidebar_layout.itemAt(self._sidebar_layout.count() - 1)
            )
            self.groups_panel.setVisible(True)

    def _hide_groups_panel(self):
        """Hide the groups panel and restore the sidebar stretch."""
        if self.groups_panel.isVisible():
            self.groups_panel.setVisible(False)
            self._sidebar_layout.addStretch()

    def _update_classifier_path(self, context: VideoSearchContext):
        """Update the classifier path display."""
        # Get classifier path from context
        self._classifier_path = list(context.classifier) if context.classifier else []

        # Check if grouping is on a multiple property (classifier is only for multiple props)
        is_multiple_property = False
        if (
            context.grouping
            and context.grouping.is_property
            and self.ctx.has_database()
        ):
            prop_types = self.ctx.get_prop_types(
                name=context.grouping.field, multiple=True
            )
            is_multiple_property = len(prop_types) > 0

        self._is_classifying = is_multiple_property

        # Show/hide classifier section based on path and property type
        has_path = len(self._classifier_path) > 0
        self.classifier_section.setVisible(has_path)

        # Show/hide the add-to-classifier button in group bar
        self.btn_add_to_classifier.setVisible(is_multiple_property)

        if not has_path:
            return

        # Clear existing path items
        while self.classifier_path_layout.count() > 0:
            item = self.classifier_path_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add path items
        for i, value in enumerate(self._classifier_path):
            item_widget = QWidget()
            item_widget.setStyleSheet("background: transparent;")
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(2, 1, 2, 1)
            item_layout.setSpacing(2)

            # Value label
            value_label = QLabel(str(value))
            value_label.setStyleSheet(
                "background: #e0e0e0; padding: 2px 4px; border-radius: 3px;"
            )
            item_layout.addWidget(value_label, 1)

            # Unstack button (only on last item)
            if i == len(self._classifier_path) - 1:
                unstack_btn = QPushButton("✕")
                unstack_btn.setFixedSize(20, 20)
                unstack_btn.setToolTip(say("Remove from path (unstack)"))
                unstack_btn.setStyleSheet(
                    "QPushButton { background-color: #cc3333; color: white; "
                    "font-weight: bold; border-radius: 3px; }"
                    "QPushButton:hover { background-color: #dd4444; }"
                )
                unstack_btn.clicked.connect(self._on_classifier_unstack)
                item_layout.addWidget(unstack_btn)

            self.classifier_path_layout.addWidget(item_widget)

    def _update_sources_display(self, sources: list[list[str]] | None):
        """Update the sources info label."""
        # Check if a source expression is active
        source_expression = self.ctx.get_source_expression()
        if source_expression:
            self.btn_sources_clear.setEnabled(True)
            text = source_expression
            if len(text) > 50:
                text = text[:47] + "..."
            self.sources_info.setText(text)
            self.sources_info.setToolTip(source_expression)
            return

        # Enable/disable clear button based on whether sources differ from default
        is_default = sources is None or sources == PYTHON_DEFAULT_SOURCES
        self.btn_sources_clear.setEnabled(not is_default)

        if not sources:
            self.sources_info.setText(say("All sources"))
            self.sources_info.setToolTip("")
            return

        # Format sources for display
        formatted = []
        for path in sources:
            if len(path) == 1:
                # Single level: "readable" or "unreadable"
                formatted.append(path[0].capitalize())
            elif len(path) == 2:
                # Two levels: "readable.found" -> "Found"
                formatted.append(path[1].replace("_", " ").capitalize())
            else:
                # Full path: "readable.found.with_thumbnails" -> "With thumbnails"
                formatted.append(path[-1].replace("_", " ").capitalize())

        # Join with commas, truncate if too long
        full_text = ", ".join(formatted)
        text = full_text
        if len(text) > 50:
            text = text[:47] + "..."
        self.sources_info.setText(text)
        self.sources_info.setToolTip(full_text if full_text != text else "")

    def _update_sorting_display(self, sorting: list[str] | None):
        """Update the sorting info label."""
        # Enable/disable clear button based on whether sorting differs from default
        is_default = sorting is None or list(sorting) == VIDEO_DEFAULT_SORTING
        self.btn_sorting_clear.setEnabled(not is_default)

        if not sorting:
            self.sorting_info.setText(say("Default"))
            return

        lines = []
        for field_name, reverse in VideoSorting(sorting):
            arrow = Uniconst.ARROW_DOWN if reverse else Uniconst.ARROW_UP
            # Get field title
            if field_name in FIELD_MAP.fields:
                title = FIELD_MAP.fields[field_name].title
            else:
                title = field_name.replace("_", " ").title()

            lines.append(f"<b>{title}</b> {arrow}")

        self.sorting_info.setText("<br>".join(lines))

    def _update_search_display(self, search):
        """Update the search mode indicator."""
        if not search or not search.text:
            self._active_search_text = ""
            self.btn_search_clear.setEnabled(False)
            if self.search_input.text():
                self.search_input.clear()
            self._highlight_search_mode(None)
            self._update_search_input_color()
            return

        self._search_mode = search.cond
        self._active_search_text = search.text

        # Update search input if it doesn't match
        if self.search_input.text() != search.text:
            self.search_input.setText(search.text)

        self.btn_search_clear.setEnabled(True)
        self._highlight_search_mode(search.cond)
        self._update_search_input_color()

    def _on_search_text_changed(self):
        """Update search input color when text changes."""
        self._update_search_input_color()

    def _update_search_input_color(self):
        """Color search input blue when text matches the active search."""
        if (
            self._active_search_text
            and self.search_input.text().strip() == self._active_search_text
        ):
            self.search_input.setStyleSheet("QLineEdit { color: #0055cc; }")
        else:
            self.search_input.setStyleSheet("")

    def _highlight_search_mode(self, cond):
        """Bold the active search mode button, unbold the others."""
        buttons = {
            "and": self.btn_search_and,
            "or": self.btn_search_or,
            "exact": self.btn_search_exact,
            "id": self.btn_search_id,
        }
        for mode, btn in buttons.items():
            font = btn.font()
            font.setBold(mode == cond)
            btn.setFont(font)

    def _update_grouping_display(self, context: VideoSearchContext):
        """Update the grouping info label with detailed information."""
        grouping = context.grouping
        if not grouping or not grouping.field:
            self.grouping_info.setText(say("No grouping"))
            self.btn_grouping_clear.setEnabled(False)
            return

        # Line 1: compact title — "field" (#) ▼
        field_name = grouping.field.replace("_", " ").title()
        if grouping.is_property:
            title = f'"{field_name}"'
        else:
            title = field_name
        if grouping.sorting == "count":
            title += " (#)"
        elif grouping.sorting == "length":
            title = f"|| {title} ||"
        title += " \u25bc" if grouping.reverse else " \u25b2"

        # Line 2: group count + singletons
        nb_groups = len(context.classifier_stats) if context.classifier_stats else 0
        count_line = say("{count} groups", count=nb_groups)
        if not grouping.allow_singletons:
            count_line += " (# > 1)"

        self.grouping_info.setText(f"{title}\n{count_line}")
        self.btn_grouping_clear.setEnabled(True)

        # Update grouped_by_moves flag and show/hide the confirm button
        self._grouped_by_moves = grouping.field == "move_id"
        self._grouped_by_similarity = grouping.field in SIMILARITY_FIELDS
        self._similarity_field = grouping.field if self._grouped_by_similarity else None
        self.btn_confirm_unique_moves.setVisible(self._grouped_by_moves)

    def _display_videos(self, videos: list[VideoPattern]):
        """Display the videos in the content area."""
        self._videos = videos
        self._display_list_view(videos)

    def _reset_scroll_to_top(self):
        """Reset the scroll position to the top."""
        self.list_widget.verticalScrollBar().setValue(0)

    def _display_list_view(self, videos: list[VideoPattern]):
        """Display videos in list view with VideoListItem widgets.

        Updates the QListWidget slot-by-slot: existing slots get a new widget
        (via setItemWidget which auto-destroys the previous one), missing
        slots are appended, extra slots are taken away. The QListWidget never
        goes through an empty state, so its scroll position is preserved
        natively across refreshes — including when the window is in
        background.
        """
        diff_fields = self._diff_fields if self._diff_fields else None

        n_old = self.list_widget.count()
        n_new = len(videos)

        # Replace existing slots: new widget on existing QListWidgetItem
        for i in range(min(n_old, n_new)):
            new_widget = self._make_video_list_item(videos[i], diff_fields)
            list_item = self.list_widget.item(i)
            self.list_widget.setItemWidget(list_item, new_widget)
            self._set_size_hint(list_item, new_widget)
            self._video_list_items[i] = new_widget

        # Append new slots if the page grew
        for i in range(n_old, n_new):
            new_widget = self._make_video_list_item(videos[i], diff_fields)
            list_item = QListWidgetItem()
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, new_widget)
            self._set_size_hint(list_item, new_widget)
            self._video_list_items.append(new_widget)

        # Drop extra slots if the page shrank
        while self.list_widget.count() > n_new:
            self.list_widget.takeItem(n_new)
        del self._video_list_items[n_new:]

    def _set_size_hint(self, list_item: QListWidgetItem, widget: QWidget):
        """Set the QListWidgetItem size hint based on the widget's height for
        the actual viewport width.

        VideoListItem contains WrappingLabels whose sizeHint is plafonned at
        400px wide. Used as-is in a wider viewport, that yields too tall a
        cell (text wrapped on more lines than necessary). Computing
        heightForWidth at the real viewport width gives the right cell size.
        """
        viewport_width = self.list_widget.viewport().width()
        sb = self.list_widget.verticalScrollBar()
        if sb.isVisible():
            viewport_width -= sb.width()
        if viewport_width > 50:
            h = widget.heightForWidth(viewport_width)
            if h > 0:
                list_item.setSizeHint(QSize(viewport_width, h))
                return
        list_item.setSizeHint(widget.sizeHint())

    def resizeEvent(self, event):
        """Recompute list item size hints when the page is resized.

        Without this, the cells keep the height computed for the viewport
        width at refresh time, even after the user resizes the window.
        """
        super().resizeEvent(event)
        for i in range(self.list_widget.count()):
            list_item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(list_item)
            if widget is not None:
                self._set_size_hint(list_item, widget)

    def _make_video_list_item(
        self, video: VideoPattern, diff_fields: set[str] | None
    ) -> VideoListItem:
        """Build a VideoListItem with all its signals wired and selection set."""
        title_diffs = self._file_title_diffs.get(video.video_id)
        item = VideoListItem(
            video, diff_fields=diff_fields, file_title_diffs=title_diffs
        )
        item.clicked.connect(self._on_video_clicked)
        item.double_clicked.connect(self._on_video_double_clicked)
        item.open_requested.connect(self._open_video)
        item.context_menu_requested.connect(self._on_video_context_menu)
        item.selection_changed.connect(self._on_video_selection_changed)
        item.property_value_clicked.connect(self._on_property_value_clicked)
        item.selected = self._selector.contains(video.video_id)
        return item

    def _on_video_clicked(self, video_id: int):
        """Handle video card click - track focused video but don't change selection."""
        self._selected_video_id = video_id

    def _on_video_selection_changed(self, video_id: int, selected: bool):
        """Handle checkbox selection change from video card/item."""
        if selected:
            self._selector.include(video_id)
        else:
            self._selector.exclude(video_id)

        self._selected_video_id = video_id
        self._update_selection_display()

    def _on_property_value_clicked(self, prop_name: str, value):
        """Handle property value click - focus on this property value."""
        self.page_number = 0
        self.ctx.focus_prop_val(prop_name, value)

    def _on_video_double_clicked(self, video_id: int):
        """Handle video card double-click (open video)."""
        self._open_video(video_id)

    def _on_video_context_menu(self, video_id: int, pos):
        """Show context menu for a video."""
        menu = LeftClickMenu(self)

        menu.addAction(say("Toggle Watched"), lambda: self._toggle_watched(video_id))
        menu.addSeparator()
        menu.addAction(say("Open"), lambda: self._open_video(video_id))
        menu.addAction(say("Open in VLC"), lambda: self._open_in_vlc(video_id))
        menu.addAction(say("Open Folder"), lambda: self._open_folder(video_id))
        menu.addSeparator()

        # Copy submenu
        copy_menu = menu.addMenu(say("Copy"))
        copy_menu.addAction(say("Copy Title"), lambda: self._copy_title(video_id))
        copy_menu.addAction(
            say("Copy File Title"), lambda: self._copy_file_title(video_id)
        )
        copy_menu.addAction(
            say("Copy File Path"), lambda: self._copy_file_path(video_id)
        )
        copy_menu.addAction(say("Copy Video ID"), lambda: self._copy_video_id(video_id))

        menu.addSeparator()
        menu.addAction(say("Rename..."), lambda: self._rename_video(video_id))
        menu.addAction(say("Move to..."), lambda: self._move_video(video_id))
        menu.addSeparator()

        # Similarity actions (for both similarity_id and similarity_id_reencoded)
        video = self._get_video_by_id(video_id)
        has_sim_actions = False
        if video:
            for sim_field, sim_label in (
                ("similarity_id", say("Similarity")),
                ("similarity_id_reencoded", say("Similarity (re-encoded)")),
            ):
                sim_val = getattr(video, sim_field, None)
                if sim_val is not None:
                    has_sim_actions = True
                    if sim_val >= 0:
                        menu.addAction(
                            say("Dismiss {label}", label=sim_label),
                            lambda f=sim_field: self._dismiss_similarity(
                                video_id, field=f
                            ),
                        )
                    menu.addAction(
                        say("Reset {label}", label=sim_label),
                        lambda f=sim_field: self._reset_similarity(video_id, field=f),
                    )
            # Generalize title actions (only when grouped by a similarity field)
            if self._grouped_by_similarity and len(self._videos) > 1:
                menu.addSeparator()
                if video.meta_title:
                    menu.addAction(
                        say("Generalize meta title into property..."),
                        lambda: self._generalize_title_to_property(
                            video_id, "meta_title"
                        ),
                    )
                menu.addAction(
                    say("Generalize file title into property..."),
                    lambda: self._generalize_title_to_property(video_id, "file_title"),
                )
            if has_sim_actions:
                menu.addSeparator()

        # Move confirmation actions (only when video has moves)
        if video and video.moves:
            move_menu = menu.addMenu(say("Confirm move to"))
            for move in video.moves:
                dst_id = move["video_id"]
                filename = move["filename"]
                # Use a default argument to capture the current dst_id value
                move_menu.addAction(
                    filename, lambda did=dst_id: self._confirm_move(video_id, did)
                )
            menu.addSeparator()

        menu.addAction(say("Properties..."), lambda: self._show_properties(video_id))
        menu.addSeparator()
        menu.addAction(
            say("Delete from database"), lambda: self._delete_video(video_id)
        )
        menu.addAction(say("Move to Trash"), lambda: self._trash_video(video_id))
        menu.addAction(
            say("Delete permanently"), lambda: self._delete_video_file(video_id)
        )

        menu.exec(pos)

    def _open_video(self, video_id: int):
        """
        Open a video with default player.

        NB: Old code would protect this call with:
            self.window().setEnabled(False)
            try:
                self.ctx.open_video(video_id)
            finally:
                self.window().setEnabled(True)

        However, open_video() does 2 things:
        - open video (OS operation)
        - notify GUI about state changed

        It should not be a real problem if interface is still active
        while these operations occur, since the outcome should be
        to update just "watched" indicator in video display. Action
        indicators or inputs are normally not impacted.

        So, we don't really need to protect this call in a
        window disabled/enabled block.
        """
        self.ctx.open_video(video_id)

    def _open_in_vlc(self, video_id: int):
        """
        Open a video in VLC via server.

        NB: See _open_video about why we don't protect
        this call in a window disabled/enabled block.
        """
        self.ctx.open_from_server(video_id)

    def _open_folder(self, video_id: int):
        """
        Open the folder containing a video.

        NB: See _open_video about why we don't protect
        this call in a window disabled/enabled block.
        """
        self.ctx.open_containing_folder(video_id)

    def _get_video_by_id(self, video_id: int):
        """Get video object by ID from current page."""
        for video in self._videos:
            if video.video_id == video_id:
                return video
        return None

    def _copy_to_clipboard(self, text: str):
        """Copy text to system clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def _copy_title(self, video_id: int):
        """Copy video title to clipboard."""
        video = self._get_video_by_id(video_id)
        if video:
            self._copy_to_clipboard(str(video.title))

    def _copy_file_title(self, video_id: int):
        """Copy video file title to clipboard."""
        video = self._get_video_by_id(video_id)
        if video:
            self._copy_to_clipboard(str(video.file_title))

    def _copy_file_path(self, video_id: int):
        """Copy video file path to clipboard."""
        video = self._get_video_by_id(video_id)
        if video:
            self._copy_to_clipboard(str(video.filename))

    def _copy_video_id(self, video_id: int):
        """Copy video ID to clipboard."""
        self._copy_to_clipboard(str(video_id))

    def _rename_video(self, video_id: int):
        """Rename video (change file title)."""
        video = self._get_video_by_id(video_id)
        if not video or not self.ctx.has_database():
            return

        current_title = str(video.file_title)
        new_title, ok = QInputDialog.getText(
            self,
            say("Rename Video"),
            say("New file title:"),
            QLineEdit.EchoMode.Normal,
            current_title,
        )

        if ok and new_title and new_title != current_title:
            try:
                self.ctx.rename_video(video_id, new_title)
            except Exception as e:
                QMessageBox.warning(self, say("Rename Failed"), str(e))

    def _dismiss_similarity(self, video_id: int, field: str = "similarity_id"):
        """Dismiss similarity for a video (mark as no match)."""
        reply = QMessageBox.question(
            self,
            say("Dismiss Similarity"),
            say(
                "Mark this video as having no similar matches?\n\n"
                "The video will be excluded from future similarity searches."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.ctx.dismiss_similarity(video_id, field=field)

    def _reset_similarity(self, video_id: int, field: str = "similarity_id"):
        """Reset similarity for a video (mark as not compared)."""
        reply = QMessageBox.question(
            self,
            say("Reset Similarity"),
            say(
                "Reset similarity status for this video?\n\n"
                "The video will be re-evaluated in the next similarity search."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.ctx.reset_similarity(video_id, field=field)

    def _generalize_title_to_property(self, video_id: int, title_field: str):
        """Copy a video's title into a property for all other videos in the group."""
        video = self._get_video_by_id(video_id)
        if not video:
            return

        title_value = str(getattr(video, title_field, "") or "")
        if not title_value:
            QMessageBox.information(
                self, say("Generalize Title"), say("Title is empty.")
            )
            return

        # Get str non-enum properties
        prop_types = self.ctx.get_prop_types()
        str_props = [
            p.name for p in prop_types if p.type == "str" and not p.enumeration
        ]
        if not str_props:
            QMessageBox.information(
                self,
                say("Generalize Title"),
                say("No string (non-enum) property available."),
            )
            return

        # Ask user to pick a property via a custom dialog with wrapping text
        nb_others = len(self._videos) - 1
        dialog = QDialog(self)
        dialog.setWindowTitle(say("Generalize Title"))
        layout = QVBoxLayout(dialog)

        label = QLabel(
            say(
                "Copy <b>{title}</b> into property for {count} other video(s):",
                title=escape(title_value),
                count=nb_others,
            )
        )
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(label)

        combo = QComboBox()
        combo.addItems(str_props)
        layout.addWidget(combo)

        buttons = QHBoxLayout()
        btn_ok = QPushButton(say("OK"))
        btn_cancel = QPushButton(say("Cancel"))
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)
        buttons.addStretch()
        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        prop_name = combo.currentText()

        # Add property value for all other videos in the group (merges with existing)
        other_ids = [v.video_id for v in self._videos if v.video_id != video_id]
        self.ctx.add_property_value_for_videos(other_ids, prop_name, [title_value])
        self.status_message_requested.emit(
            say(
                'Property "{name}" set to "{value}" for {count} video(s)',
                name=prop_name,
                value=title_value,
                count=len(other_ids),
            ),
            5000,
        )

    def _confirm_move(self, src_video_id: int, dst_video_id: int):
        """Confirm a video move (transfer metadata from source to destination)."""
        src_video = self._get_video_by_id(src_video_id)
        if not src_video:
            return

        # Find destination filename from moves
        dst_filename = None
        for move in src_video.moves or []:
            if move["video_id"] == dst_video_id:
                dst_filename = move["filename"]
                break

        reply = QMessageBox.question(
            self,
            say("Confirm Move"),
            say(
                "Transfer metadata from missing video to:\n\n{filename}\n\n"
                "The missing video entry will be deleted.",
                filename=dst_filename,
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.ctx.confirm_move(src_video_id, dst_video_id)
            self._purge_video_from_selection(src_video_id)
            self.status_message_requested.emit(say("Video move confirmed"), 3000)

    def _on_confirm_unique_moves(self):
        """Confirm all unique video moves (videos with only one possible destination)."""
        reply = QMessageBox.question(
            self,
            say("Confirm All Unique Moves"),
            say(
                "This will automatically confirm all video moves that have only "
                "one possible destination.\n\n"
                "The metadata from missing videos will be transferred to the "
                "found files, and the missing entries will be deleted.\n\n"
                "Continue?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.btn_confirm_unique_moves.setEnabled(False)
            try:
                count = self.ctx.confirm_unique_moves()
                self._clear_selection()
                self.status_message_requested.emit(
                    say("Confirmed {count} video move(s)", count=count), 3000
                )
            finally:
                self.btn_confirm_unique_moves.setEnabled(True)

    def _toggle_watched(self, video_id: int):
        """Toggle the watched status of a video."""
        self.ctx.toggle_watched(video_id)

    def _on_toggle_watched_selection(self):
        """Toggle watched status for all selected videos."""
        video_ids = self._selected_video_ids
        if not video_ids:
            return
        self.ctx.toggle_watched_many(video_ids)

    def _move_video(self, video_id: int):
        """Move a video file to a different folder."""
        if not self.ctx.has_database():
            return

        # Get database folders for initial directory
        folders = self.ctx.get_database_folders()
        initial_dir = folders[0] if folders else ""

        # Show folder selection dialog
        directory = QFileDialog.getExistingDirectory(
            self, say("Move Video To"), initial_dir, QFileDialog.Option.ShowDirsOnly
        )

        if not directory:
            return

        # Confirm the move
        video = self.ctx.get_video_by_id(video_id)
        if not video:
            return

        reply = QMessageBox.question(
            self,
            say("Move Video"),
            say(
                "Move '{title}' to:\n{directory}?",
                title=video.title,
                directory=directory,
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Emit signal - MainWindow will handle showing process page and running operation
            self.move_video_requested.emit(video_id, directory)

    def _show_properties(self, video_id: int):
        """Show properties dialog for a video."""
        if not self.ctx.has_database():
            return

        video = self.ctx.get_video_by_id(video_id)
        if not video:
            return

        prop_types = self.ctx.get_prop_types()
        dialog = VideoPropertiesDialog(video, prop_types, self.ctx, self)
        dialog.exec()

    def _delete_video(self, video_id: int):
        """Delete a single video from the database (with confirmation)."""
        if not self.ctx.has_database():
            return

        # Get video from current page (VideoPattern has found property)
        video = self._get_video_by_id(video_id)
        if not video:
            # Fallback to database query
            video_entry = self.ctx.get_video_by_id(video_id)
            if not video_entry:
                return
            video_title = video_entry.meta_title or video_entry.filename
            is_not_found = not video_entry.is_file
        else:
            video_title = str(video.title)
            is_not_found = video.not_found

        # Skip confirmation for "not found" entries if option is disabled
        if is_not_found and not self.confirm_not_found_deletion:
            self.ctx.delete_video_entry(video_id)
            self._purge_video_from_selection(video_id)
            self.status_message_requested.emit(
                say("'{title}' removed from database", title=video_title), 3000
            )
            return

        confirm_video = video or self.ctx.get_video_by_id(video_id)
        if confirm_video and VideoConfirmDialog.confirm(
            say("Delete Video"),
            say(
                "Delete this video from the database?\n\n"
                "(The file will NOT be deleted from disk)"
            ),
            confirm_video,
            self,
        ):
            self.ctx.delete_video_entry(video_id)
            self._purge_video_from_selection(video_id)
            self.status_message_requested.emit(
                say("'{title}' removed from database", title=video_title), 5000
            )

    def _trash_video(self, video_id: int):
        """Move a video file to system trash (with confirmation)."""
        video = self.ctx.get_video_by_id(video_id)
        if not video:
            return

        if VideoConfirmDialog.confirm(
            say("Move to Trash"),
            say(
                "Move this video to the system trash?\n\n"
                "(The file can be restored from the trash if needed)"
            ),
            video,
            self,
        ):
            try:
                self.ctx.trash_video(video_id)
                self._purge_video_from_selection(video_id)
                self.status_message_requested.emit(
                    say("'{title}' moved to trash", title=video.title), 5000
                )
            except Exception as e:
                QMessageBox.warning(
                    self, say("Error"), say("Failed to move to trash: {error}", error=e)
                )

    def _delete_video_file(self, video_id: int):
        """Permanently delete a video file (with confirmation)."""
        video = self.ctx.get_video_by_id(video_id)
        if not video:
            return

        if VideoConfirmDialog.confirm(
            say("Delete Permanently"),
            say(
                "PERMANENTLY delete this video?\n\n"
                "This action cannot be undone!\n"
                "The file will be deleted from disk."
            ),
            video,
            self,
        ):
            try:
                self.ctx.delete_video_file(video_id)
                self._purge_video_from_selection(video_id)
                self.status_message_requested.emit(
                    say("'{title}' permanently deleted", title=video.title), 5000
                )
            except Exception as e:
                QMessageBox.warning(
                    self, say("Error"), say("Failed to delete: {error}", error=e)
                )

    def _on_batch_edit(self):
        """Show menu of properties to batch edit for selected videos."""
        selection_count = self._selector.size_from(self._view_count)
        if selection_count == 0 or not self.ctx.has_database():
            return

        prop_types = self.ctx.get_prop_types()
        if not prop_types:
            QMessageBox.information(
                self,
                say("No Properties"),
                say(
                    "No custom properties defined.\n"
                    "Create properties in the Properties page first."
                ),
            )
            return

        # Show menu of properties to choose from
        menu = LeftClickMenu(self)
        for prop_type in prop_types:
            prop_name = prop_type.name
            action = menu.addAction(prop_name)
            action.setData(prop_type)

        # Show menu at cursor position
        action = menu.exec(QCursor.pos())
        if action:
            prop_type = action.data()
            self._edit_property_for_selection(prop_type)

    def _edit_property_for_selection(self, prop_type: PropType):
        """Edit a specific property for selected videos."""
        if not self.ctx.has_database():
            return

        prop_name = prop_type.name
        selection_count = self._selector.size_from(self._view_count)

        # Get current values and counts using apply_on_view
        selector_dict = self._selector.to_dict()
        values_and_counts = self.ctx.query_on_view(
            selector_dict, "count_property_values", prop_name
        )

        if values_and_counts is None:
            values_and_counts = []

        # Show the batch edit property dialog
        result = BatchEditPropertyDialog.edit_property(
            prop_name=prop_name,
            prop_type=prop_type,
            nb_videos=selection_count,
            values_and_counts=values_and_counts,
            parent=self,
        )

        if result:
            to_add, to_remove = result
            if to_add or to_remove:
                # Apply changes using apply_on_view
                self.ctx.apply_on_view(
                    selector_dict,
                    "edit_property_for_videos",
                    prop_name,
                    to_add,
                    to_remove,
                )

    def _on_page_size_changed(self, text: str):
        """Handle page size change."""
        self.page_size = int(text)
        self.page_number = 0
        self.refresh()

    def _on_edit_sources(self):
        """Handle edit sources button (simple tab)."""
        self._open_sources_dialog(start_tab=0)

    def _on_edit_source_expression(self):
        """Handle edit source expression shortcut (advanced tab)."""
        self._open_sources_dialog(start_tab=1)

    def _open_sources_dialog(self, start_tab: int = 0):
        """Open the sources dialog on the given tab."""
        current_sources = None
        current_expression = None
        state = self.ctx.get_provider_state()
        if state:
            current_sources = state.sources if hasattr(state, "sources") else None
        current_expression = self.ctx.get_source_expression()

        dialog = SourcesDialog(
            current_sources, current_expression, self, start_tab=start_tab
        )
        if dialog.exec():
            self.page_number = 0
            if dialog.is_advanced():
                self.ctx.set_source_expression(dialog.get_expression())
            else:
                self.ctx.set_sources(dialog.get_sources())

    def _on_set_grouping(self):
        """Handle set grouping button."""
        # Get current grouping
        current_grouping = None
        state = self.ctx.get_provider_state()
        if state and state.grouping:
            current_grouping = {
                "field": state.grouping.field,
                "is_property": state.grouping.is_property,
                "sorting": state.grouping.sorting,
                "reverse": state.grouping.reverse,
                "allow_singletons": state.grouping.allow_singletons,
            }

        # Get property types
        prop_types = self.ctx.get_prop_types()

        dialog = GroupingDialog(prop_types, current_grouping, self)
        if dialog.exec():
            grouping = dialog.get_grouping()
            self.page_number = 0
            if grouping is None:
                # Clear grouping
                self.ctx.clear_groups()
            else:
                self.ctx.set_groups(
                    field=grouping["field"],
                    is_property=grouping["is_property"],
                    sorting=grouping["sorting"],
                    reverse=grouping["reverse"],
                    allow_singletons=grouping["allow_singletons"],
                )

    def _on_search_and(self):
        self._do_search("and")

    def _on_search_or(self):
        self._do_search("or")

    def _on_search_exact(self):
        self._do_search("exact")

    def _on_search_id(self):
        self._do_search("id")

    def _on_search(self):
        """Handle search on Enter key, reusing the current search mode."""
        self._do_search(self._search_mode)

    def _do_search(self, mode: str):
        """Perform search with given mode."""
        query = self.search_input.text().strip()
        if query:
            self.page_number = 0
            self.ctx.set_search(query, mode)
            # Release focus so a subsequent Ctrl+A/Ctrl+Shift+A/Delete/...
            # reaches the page shortcut instead of being consumed by the
            # QLineEdit's own standard editing shortcuts (e.g. select-all-text).
            self.search_input.clearFocus()

    def _clear_search(self):
        """Clear the search."""
        self.search_input.clear()
        self._search_mode = "and"
        self.page_number = 0
        self.ctx.set_search("", "and")

    def _clear_sources(self):
        """Reset sources to default."""
        self.page_number = 0
        self.ctx.set_source_expression(None)
        self.ctx.set_sources(None)

    def _clear_grouping(self):
        """Remove grouping."""
        self.page_number = 0
        self.ctx.clear_groups()

    def _clear_sorting(self):
        """Reset sorting to default."""
        self.page_number = 0
        self.ctx.set_sorting(None)

    def _on_set_sorting(self):
        """Handle set sorting button."""
        # Get current sorting
        current_sorting = None
        state = self.ctx.get_provider_state()
        if state and state.sorting:
            video_sorting = state.get_video_sorting()
            current_sorting = list(video_sorting)  # list of (field, reverse) tuples

        dialog = SortingDialog(current_sorting, self)
        if dialog.exec():
            sorting_tuples = dialog.get_sorting()
            # Convert (field, reverse) tuples to "-field" or "+field" strings
            sorting_strings = [
                f"-{field}" if reverse else f"+{field}"
                for field, reverse in sorting_tuples
            ]
            self.page_number = 0
            self.ctx.set_sorting(sorting_strings)

    def _on_random_video(self):
        """Open a random video and configure search to show it."""
        # We need window disabled/enabled protection here
        # because this action will modify many displays,
        # including action inputs (e.g. grouping, searching).
        self.window().setEnabled(False)
        try:
            self.page_number = 0
            search_text = self.ctx.open_random_video()
            if search_text:
                self.search_input.setText(search_text)
        finally:
            self.window().setEnabled(True)

    def _on_update_database(self):
        """Update/rescan the database."""
        reply = QMessageBox.question(
            self,
            say("Update Database"),
            say(
                "Rescan folders and update the database?\n\n"
                "This may take a while depending on the number of videos."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.update_database_requested.emit()

    def _on_find_similar(self):
        """Find similar videos."""
        reply = QMessageBox.question(
            self,
            say("Find Similar Videos"),
            say(
                "Search for visually similar videos?\n\n"
                "This may take a while depending on the number of videos."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.find_similar_requested.emit()

    def _on_find_reencoded(self):
        """Find potentially re-encoded videos."""
        reply = QMessageBox.question(
            self,
            say("Find Re-encoded Videos"),
            say(
                "Search for potentially re-encoded videos?\n\n"
                "Compares filenames and durations to find videos\n"
                "that may be re-encodings of the same source."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.find_similar_reencoded_requested.emit()

    # =========================================================================
    # Classifier operations
    # =========================================================================

    def _on_classifier_add_group(self):
        """Add the current group to the classifier path."""
        if self._current_group_index >= 0:
            self.page_number = 0
            self.ctx.classifier_select_group(self._current_group_index)

    def _on_classifier_unstack(self):
        """Remove the last value from the classifier path."""
        if self._classifier_path:
            self.page_number = 0
            self.ctx.classifier_back()

    def _on_classifier_reverse(self):
        """Reverse the classifier path order."""
        if self._classifier_path:
            self.ctx.classifier_reverse()

    def _on_classifier_concatenate(self):
        """Show dialog to concatenate path values into a string property."""
        if not self._classifier_path or not self.ctx.has_database():
            return

        # Get string properties to concatenate into
        prop_types = self.ctx.get_prop_types()
        string_props = [p for p in prop_types if p.type == "str"]

        if not string_props:
            QMessageBox.information(
                self,
                say("No Target Property"),
                say(
                    "No single-value string properties available.\n\n"
                    "Create a string property first to concatenate the path into."
                ),
            )
            return

        # Show selection dialog
        prop_names = [p.name for p in string_props]
        name, ok = QInputDialog.getItem(
            self,
            say("Concatenate Path"),
            say("Select target property to concatenate path values into:"),
            prop_names,
            0,
            False,
        )

        if ok and name:
            self.ctx.classifier_concatenate_path(name)
            self.page_number = 0

    def _go_prev_group(self):
        """Go to the previous group."""
        if self._current_group_index > 0:
            new_index = self._current_group_index - 1
            self._select_group(new_index)

    def _go_next_group(self):
        """Go to the next group."""
        if (
            self._current_group_index >= 0
            and self._current_group_index < len(self._group_stats) - 1
        ):
            new_index = self._current_group_index + 1
            self._select_group(new_index)

    def _go_first_group(self):
        """Go to the first group."""
        if self._group_stats and self._current_group_index != 0:
            self._select_group(0)

    def _go_last_group(self):
        """Go to the last group."""
        if self._group_stats:
            last_index = len(self._group_stats) - 1
            if self._current_group_index != last_index:
                self._select_group(last_index)

    def _on_group_list_selected(self, row: int):
        """Handle group selection from sidebar list."""
        if row >= 0 and row != self._current_group_index:
            self._select_group(row)

    def _select_group(self, index: int):
        """Select a group by index."""
        if not self._group_stats or index < 0 or index >= len(self._group_stats):
            return

        self.page_number = 0
        self.ctx.set_group(index)
        self._reset_scroll_to_top()

    def _on_go_to_page(self):
        """Show dialog to go to a specific page."""
        page = GoToPageDialog.get_page_number(
            current_page=self.page_number + 1,
            total_pages=self._total_pages,
            parent=self,
        )
        if page is not None and page != self.page_number:
            self.page_number = page
            self.refresh()
            self._reset_scroll_to_top()

    def _go_first(self):
        """Go to first page."""
        self.page_number = 0
        self.refresh()
        self._reset_scroll_to_top()

    def _go_prev(self):
        """Go to previous page."""
        if self.page_number > 0:
            self.page_number -= 1
            self.refresh()
            self._reset_scroll_to_top()

    def _go_next(self):
        """Go to next page."""
        self.page_number += 1
        self.refresh()
        self._reset_scroll_to_top()

    def _go_last(self):
        """Go to last page."""
        if self.ctx.has_database():
            context = self.ctx.get_videos(self.page_size, 0)
            self.page_number = max(0, context.nb_pages - 1)
            self.refresh()
            self._reset_scroll_to_top()

    def _go_to_properties(self):
        """Navigate to properties page."""
        main_window = self.window()
        if hasattr(main_window, "show_properties_page"):
            main_window.show_properties_page()
