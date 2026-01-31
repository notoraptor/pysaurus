"""
Videos page for browsing and managing videos.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from pysaurus.video_provider.field_stat import FieldStat

from pysaurus.interface.pyside6.app_context import AppContext
from pysaurus.interface.pyside6.dialogs import (
    GroupingDialog,
    SortingDialog,
    SourcesDialog,
    VideoPropertiesDialog,
)
from pysaurus.interface.pyside6.widgets.flow_layout import FlowLayout
from pysaurus.interface.pyside6.widgets.video_card import VideoCard
from pysaurus.interface.pyside6.widgets.video_list_item import VideoListItem
from pysaurus.video.video_pattern import VideoPattern
from pysaurus.video.video_search_context import VideoSearchContext


class VideosPage(QWidget):
    """
    Main page for browsing videos.

    Layout:
    - Toolbar at top
    - Splitter with sidebar (filters) and content (video grid/list)
    - Pagination at bottom
    """

    # Signal emitted when a long operation is requested
    long_operation_requested = Signal()

    VIEW_GRID = 0
    VIEW_LIST = 1

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.page_size = 20
        self.page_number = 0
        self._video_cards: list[VideoCard] = []
        self._video_list_items: list[VideoListItem] = []
        self._videos: list[VideoPattern] = []  # Current videos for list view
        self._selected_video_id: int | None = None
        self._group_stats: list[FieldStat] = []
        self._current_group_index: int = -1
        self._current_view = self.VIEW_LIST
        self._selected_video_ids: set[int] = set()  # For multiple selection
        self._last_clicked_index: int = -1  # For Shift+Click range selection
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

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

        # Ctrl+A - Select all
        shortcut_select_all = QShortcut(QKeySequence("Ctrl+A"), self)
        shortcut_select_all.activated.connect(self._select_all)

        # Escape - Clear selection
        shortcut_escape = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        shortcut_escape.activated.connect(self._clear_selection)

        # Enter - Open selected video
        shortcut_enter = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        shortcut_enter.activated.connect(self._open_selected)

        # Delete - Delete selected
        shortcut_delete = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        shortcut_delete.activated.connect(self._delete_selected)

        # Home/End - First/Last page
        shortcut_home = QShortcut(QKeySequence(Qt.Key.Key_Home), self)
        shortcut_home.activated.connect(self._go_first)

        shortcut_end = QShortcut(QKeySequence(Qt.Key.Key_End), self)
        shortcut_end.activated.connect(self._go_last)

    def _focus_search(self):
        """Focus the search input."""
        self.search_input.setFocus()
        self.search_input.selectAll()

    def _select_all(self):
        """Select all videos on the current page."""
        self._selected_video_ids = {v.video_id for v in self._videos}
        self._update_selection_display()

    def _clear_selection(self):
        """Clear video selection."""
        self._selected_video_ids.clear()
        self._selected_video_id = None
        self._update_selection_display()

    def _update_selection_display(self):
        """Update the visual display of selected videos."""
        if self._current_view == self.VIEW_GRID:
            for card in self._video_cards:
                card.selected = card.video.video_id in self._selected_video_ids
        else:
            # Update list item selection
            for item in self._video_list_items:
                item.selected = item.video.video_id in self._selected_video_ids

        # Update selection indicator and batch action buttons
        count = len(self._selected_video_ids)
        if count > 1:
            self.selection_label.setText(f"{count} selected")
            self.btn_batch_edit.setVisible(True)
            self.btn_clear_selection.setVisible(True)
        else:
            self.selection_label.setText("")
            self.btn_batch_edit.setVisible(False)
            self.btn_clear_selection.setVisible(False)

    def _open_selected(self):
        """Open the selected video(s)."""
        if self._selected_video_id and self.ctx.ops:
            self.ctx.ops.open_video(self._selected_video_id)
        elif self._selected_video_ids and self.ctx.ops:
            # Open the first selected video
            video_id = next(iter(self._selected_video_ids))
            self.ctx.ops.open_video(video_id)

    def _delete_selected(self):
        """Delete the selected video(s) from the database."""
        if not self._selected_video_ids and not self._selected_video_id:
            return

        video_ids = self._selected_video_ids or {self._selected_video_id}
        count = len(video_ids)

        reply = QMessageBox.question(
            self,
            "Delete Videos",
            f"Delete {count} video(s) from the database?\n\n"
            "(Files will NOT be deleted from disk)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.ctx.database:
                for video_id in video_ids:
                    self.ctx.database.video_entry_del(video_id)
                self._clear_selection()
                self.refresh()

    def _create_toolbar(self) -> QToolBar:
        """Create the toolbar."""
        toolbar = QToolBar()

        # Refresh button
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setToolTip("Refresh video list (Ctrl+R)")
        self.btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(self.btn_refresh)

        toolbar.addSeparator()

        # View toggle
        toolbar.addWidget(QLabel("View:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Grid", "List"])
        self.view_combo.setCurrentIndex(self._current_view)
        self.view_combo.currentIndexChanged.connect(self._on_view_changed)
        toolbar.addWidget(self.view_combo)

        toolbar.addSeparator()

        # Random video button
        self.btn_random = QPushButton("Random")
        self.btn_random.setToolTip("Open a random video (Ctrl+O)")
        self.btn_random.clicked.connect(self._on_random_video)
        toolbar.addWidget(self.btn_random)

        # Find similar button
        self.btn_similar = QPushButton("Find Similar")
        self.btn_similar.setToolTip("Find visually similar videos")
        self.btn_similar.clicked.connect(self._on_find_similar)
        toolbar.addWidget(self.btn_similar)

        toolbar.addSeparator()

        # Page size
        toolbar.addWidget(QLabel("Per page:"))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["10", "20", "50", "100"])
        self.page_size_combo.setCurrentText("20")
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        toolbar.addWidget(self.page_size_combo)

        toolbar.addSeparator()

        # Selection indicator and batch actions
        self.selection_label = QLabel("")
        self.selection_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        toolbar.addWidget(self.selection_label)

        self.btn_batch_edit = QPushButton("Edit Properties...")
        self.btn_batch_edit.setToolTip("Edit properties for selected videos")
        self.btn_batch_edit.clicked.connect(self._on_batch_edit)
        self.btn_batch_edit.setVisible(False)
        toolbar.addWidget(self.btn_batch_edit)

        self.btn_clear_selection = QPushButton("Clear Selection")
        self.btn_clear_selection.setToolTip("Clear selection (Escape)")
        self.btn_clear_selection.clicked.connect(self._clear_selection)
        self.btn_clear_selection.setVisible(False)
        toolbar.addWidget(self.btn_clear_selection)

        return toolbar

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
        sidebar.setMaximumWidth(180)
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
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)

        # Sources section
        sources_section, sources_layout = self._create_filter_section(color_light)
        sources_label = QLabel("Sources")
        sources_label.setStyleSheet("font-weight: bold; background: transparent;")
        sources_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sources_layout.addWidget(sources_label)

        self.sources_info = QLabel("All readable")
        self.sources_info.setStyleSheet("color: #555; background: transparent;")
        self.sources_info.setWordWrap(True)
        self.sources_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sources_layout.addWidget(self.sources_info)

        sources_btn_layout = QHBoxLayout()
        sources_btn_layout.setSpacing(2)
        self.btn_sources = QPushButton("Edit...")
        self.btn_sources.setToolTip("Edit video sources (Ctrl+T)")
        self.btn_sources.clicked.connect(self._on_edit_sources)
        sources_btn_layout.addWidget(self.btn_sources)

        self.btn_sources_clear = QPushButton("✕")
        self.btn_sources_clear.setObjectName("clearBtn")
        self.btn_sources_clear.setToolTip("Reset to default sources")
        self.btn_sources_clear.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        self.btn_sources_clear.clicked.connect(self._clear_sources)
        sources_btn_layout.addWidget(self.btn_sources_clear)
        sources_layout.addLayout(sources_btn_layout)
        layout.addWidget(sources_section)

        # Grouping section
        grouping_section, grouping_layout = self._create_filter_section(color_lighter)
        grouping_label = QLabel("Grouping")
        grouping_label.setStyleSheet("font-weight: bold; background: transparent;")
        grouping_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grouping_layout.addWidget(grouping_label)

        self.grouping_info = QLabel("No grouping")
        self.grouping_info.setStyleSheet("color: #555; background: transparent;")
        self.grouping_info.setWordWrap(True)
        self.grouping_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grouping_layout.addWidget(self.grouping_info)

        grouping_btn_layout = QHBoxLayout()
        grouping_btn_layout.setSpacing(2)
        self.btn_grouping = QPushButton("Set...")
        self.btn_grouping.setToolTip("Configure video grouping (Ctrl+G)")
        self.btn_grouping.clicked.connect(self._on_set_grouping)
        grouping_btn_layout.addWidget(self.btn_grouping)

        self.btn_grouping_clear = QPushButton("✕")
        self.btn_grouping_clear.setObjectName("clearBtn")
        self.btn_grouping_clear.setToolTip("Remove grouping")
        self.btn_grouping_clear.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        self.btn_grouping_clear.clicked.connect(self._clear_grouping)
        grouping_btn_layout.addWidget(self.btn_grouping_clear)
        grouping_layout.addLayout(grouping_btn_layout)
        layout.addWidget(grouping_section)

        # Search section
        search_section, search_layout = self._create_filter_section(color_light)
        search_label = QLabel("Search")
        search_label.setStyleSheet("font-weight: bold; background: transparent;")
        search_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search... (Ctrl+F)")
        self.search_input.setToolTip("Search videos (Ctrl+F)")
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        # Search mode indicator
        self.search_mode_label = QLabel("")
        self.search_mode_label.setStyleSheet(
            "color: #0078d4; font-style: italic; background: transparent;"
        )
        self.search_mode_label.setWordWrap(True)
        self.search_mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        search_layout.addWidget(self.search_mode_label)

        # First row: AND, OR buttons
        search_btn_layout1 = QHBoxLayout()
        search_btn_layout1.setSpacing(2)
        self.btn_search_and = QPushButton("AND")
        self.btn_search_and.setToolTip("Search for all terms")
        self.btn_search_and.clicked.connect(lambda: self._do_search("and"))
        search_btn_layout1.addWidget(self.btn_search_and)

        self.btn_search_or = QPushButton("OR")
        self.btn_search_or.setToolTip("Search for any term")
        self.btn_search_or.clicked.connect(lambda: self._do_search("or"))
        search_btn_layout1.addWidget(self.btn_search_or)
        search_layout.addLayout(search_btn_layout1)

        # Second row: Exact, ID, Clear buttons
        search_btn_layout2 = QHBoxLayout()
        search_btn_layout2.setSpacing(2)
        self.btn_search_exact = QPushButton("Exact")
        self.btn_search_exact.setToolTip("Search for exact sentence")
        self.btn_search_exact.clicked.connect(lambda: self._do_search("exact"))
        search_btn_layout2.addWidget(self.btn_search_exact)

        self.btn_search_id = QPushButton("ID")
        self.btn_search_id.setToolTip("Search by video ID")
        self.btn_search_id.clicked.connect(lambda: self._do_search("id"))
        search_btn_layout2.addWidget(self.btn_search_id)

        self.btn_search_clear = QPushButton("✕")
        self.btn_search_clear.setObjectName("clearBtn")
        self.btn_search_clear.setToolTip("Clear search")
        self.btn_search_clear.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        self.btn_search_clear.clicked.connect(self._clear_search)
        search_btn_layout2.addWidget(self.btn_search_clear)
        search_layout.addLayout(search_btn_layout2)
        layout.addWidget(search_section)

        # Sorting section
        sorting_section, sorting_layout = self._create_filter_section(color_lighter)
        sorting_label = QLabel("Sorting")
        sorting_label.setStyleSheet("font-weight: bold; background: transparent;")
        sorting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sorting_layout.addWidget(sorting_label)

        self.sorting_info = QLabel("Date ▼")
        self.sorting_info.setStyleSheet("color: #555; background: transparent;")
        self.sorting_info.setWordWrap(True)
        self.sorting_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sorting_layout.addWidget(self.sorting_info)

        sorting_btn_layout = QHBoxLayout()
        sorting_btn_layout.setSpacing(2)
        self.btn_sorting = QPushButton("Set...")
        self.btn_sorting.setToolTip("Configure video sorting (Ctrl+Shift+S)")
        self.btn_sorting.clicked.connect(self._on_set_sorting)
        sorting_btn_layout.addWidget(self.btn_sorting)

        self.btn_sorting_clear = QPushButton("✕")
        self.btn_sorting_clear.setObjectName("clearBtn")
        self.btn_sorting_clear.setToolTip("Reset to default sorting")
        self.btn_sorting_clear.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        self.btn_sorting_clear.clicked.connect(self._clear_sorting)
        sorting_btn_layout.addWidget(self.btn_sorting_clear)
        sorting_layout.addLayout(sorting_btn_layout)
        layout.addWidget(sorting_section)

        layout.addStretch()

        # Back to databases button
        self.btn_databases = QPushButton("Back to Databases")
        self.btn_databases.clicked.connect(self._on_back_to_databases)
        layout.addWidget(self.btn_databases)

        # Apply reduced font size to all buttons in sidebar
        for btn in sidebar.findChildren(QPushButton):
            font = btn.font()
            font.setPointSizeF(font.pointSizeF() * 0.8)
            btn.setFont(font)

        return sidebar

    def _create_content_area(self) -> QWidget:
        """Create the main content area for videos."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        # Group navigation bar (hidden by default)
        self.group_bar = self._create_group_bar()
        self.group_bar.setVisible(False)
        layout.addWidget(self.group_bar)

        # Stacked widget for grid/list views
        self.view_stack = QStackedWidget()
        layout.addWidget(self.view_stack)

        # Grid view (index 0)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.video_container = QWidget()
        self.video_flow = FlowLayout(
            self.video_container, margin=5, h_spacing=10, v_spacing=10
        )
        self.scroll_area.setWidget(self.video_container)
        self.view_stack.addWidget(self.scroll_area)

        # List view (index 1) - simple QWidget with layout inside scroll area
        self.list_scroll_area = QScrollArea()
        self.list_scroll_area.setWidgetResizable(True)
        self.list_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(5)
        self.list_layout.setContentsMargins(5, 5, 5, 5)
        self.list_layout.addStretch()  # Push items to top, absorb extra space
        self.list_scroll_area.setWidget(self.list_container)

        self.view_stack.addWidget(self.list_scroll_area)

        # Set initial view
        self.view_stack.setCurrentIndex(self._current_view)

        # Stats bar (at bottom)
        self.stats_label = QLabel("0 videos | 0 B | 0:00:00")
        self.stats_label.setStyleSheet("font-size: 12px; padding: 5px;")
        layout.addWidget(self.stats_label)

        return content

    def _create_group_bar(self) -> QWidget:
        """Create the group navigation bar."""
        bar = QFrame()
        bar.setFrameStyle(QFrame.Shape.StyledPanel)
        bar.setStyleSheet("QFrame { background-color: #f0f0f0; border-radius: 4px; }")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 4, 8, 4)

        # Group label
        self.group_field_label = QLabel("Group:")
        self.group_field_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.group_field_label)

        # First group button
        self.btn_first_group = QPushButton("<<")
        self.btn_first_group.setFixedWidth(30)
        self.btn_first_group.setToolTip("First group")
        self.btn_first_group.clicked.connect(self._go_first_group)
        layout.addWidget(self.btn_first_group)

        # Previous group button
        self.btn_prev_group = QPushButton("<")
        self.btn_prev_group.setFixedWidth(30)
        self.btn_prev_group.setToolTip("Previous group (Up arrow)")
        self.btn_prev_group.clicked.connect(self._go_prev_group)
        layout.addWidget(self.btn_prev_group)

        # Group selector dropdown
        self.group_combo = QComboBox()
        self.group_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.group_combo.setMinimumWidth(200)
        self.group_combo.currentIndexChanged.connect(self._on_group_selected)
        layout.addWidget(self.group_combo)

        # Next group button
        self.btn_next_group = QPushButton(">")
        self.btn_next_group.setFixedWidth(30)
        self.btn_next_group.setToolTip("Next group (Down arrow)")
        self.btn_next_group.clicked.connect(self._go_next_group)
        layout.addWidget(self.btn_next_group)

        # Last group button
        self.btn_last_group = QPushButton(">>")
        self.btn_last_group.setFixedWidth(30)
        self.btn_last_group.setToolTip("Last group")
        self.btn_last_group.clicked.connect(self._go_last_group)
        layout.addWidget(self.btn_last_group)

        # Group count label
        self.group_count_label = QLabel("0/0")
        self.group_count_label.setMinimumWidth(60)
        self.group_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.group_count_label)

        return bar

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
        self.btn_first.setToolTip("First page (Home)")
        self.btn_first.clicked.connect(self._go_first)
        layout.addWidget(self.btn_first)

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedSize(32, 24)
        self.btn_prev.setToolTip("Previous page (Left arrow)")
        self.btn_prev.clicked.connect(self._go_prev)
        layout.addWidget(self.btn_prev)

        self.page_label = QLabel("Page 1/1")
        self.page_label.setMinimumWidth(80)
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.page_label)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedSize(32, 24)
        self.btn_next.setToolTip("Next page (Right arrow)")
        self.btn_next.clicked.connect(self._go_next)
        layout.addWidget(self.btn_next)

        self.btn_last = QPushButton(">>")
        self.btn_last.setFixedSize(32, 24)
        self.btn_last.setToolTip("Last page (End)")
        self.btn_last.clicked.connect(self._go_last)
        layout.addWidget(self.btn_last)

        layout.addStretch()
        return bar

    def refresh(self):
        """Refresh the video list."""
        if not self.ctx.provider:
            return

        # Get videos from provider
        context: VideoSearchContext = self.ctx.get_videos(
            self.page_size, self.page_number
        )

        # Update stats
        self.stats_label.setText(
            f"{context.view_count} videos | "
            f"{context.selection_file_size} | "
            f"{context.selection_duration}"
        )

        # Update pagination
        nb_pages = max(1, context.nb_pages)
        self.page_label.setText(f"Page {self.page_number + 1}/{nb_pages}")

        # Update pagination button states
        self.btn_first.setEnabled(self.page_number > 0)
        self.btn_prev.setEnabled(self.page_number > 0)
        self.btn_next.setEnabled(self.page_number < nb_pages - 1)
        self.btn_last.setEnabled(self.page_number < nb_pages - 1)

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
            if (
                context.group_id is None
                and context.classifier_stats
                and self.ctx.provider
            ):
                self.ctx.provider.set_group(0)
                # Re-fetch videos with the selected group
                context = self.ctx.get_videos(self.page_size, self.page_number)
                self._current_group_index = 0
        else:
            self.grouping_info.setText("No grouping")
            self.group_bar.setVisible(False)
            self._group_stats = []
            self._current_group_index = -1

        # Display videos
        self._display_videos(context.result)

    def _update_group_bar(self, context: VideoSearchContext):
        """Update the group navigation bar."""
        self._group_stats = context.classifier_stats or []

        if not self._group_stats:
            self.group_bar.setVisible(False)
            self._current_group_index = -1
            return

        # Show the group bar
        self.group_bar.setVisible(True)

        # Update field label
        field_name = context.grouping.field if context.grouping else "Group"
        self.group_field_label.setText(f"{field_name}:")

        # Get current group index (group_id is the index)
        if context.group_id is not None and 0 <= context.group_id < len(
            self._group_stats
        ):
            self._current_group_index = context.group_id
        else:
            self._current_group_index = 0 if self._group_stats else -1

        # Populate combo box (block signals during update)
        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        for stat in self._group_stats:
            # Format: "value (count)"
            value_str = str(stat.value) if stat.value is not None else "(No value)"
            self.group_combo.addItem(f"{value_str} ({stat.count})", stat.value)
        if self._current_group_index >= 0:
            self.group_combo.setCurrentIndex(self._current_group_index)
        self.group_combo.blockSignals(False)

        # Update count label
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

    def _update_sources_display(self, sources: list[list[str]] | None):
        """Update the sources info label."""
        if not sources:
            self.sources_info.setText("All sources")
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
        text = ", ".join(formatted)
        if len(text) > 50:
            text = text[:47] + "..."
        self.sources_info.setText(text)

    def _update_sorting_display(self, sorting: list[str] | None):
        """Update the sorting info label."""
        from pysaurus.interface.common.common import FIELD_MAP, Uniconst

        if not sorting:
            self.sorting_info.setText("Default")
            return

        lines = []
        for sort_str in sorting:
            # Parse "-field" or "+field" format
            if sort_str.startswith("-"):
                field_name = sort_str[1:]
                arrow = Uniconst.ARROW_DOWN  # ▼ for descending
            elif sort_str.startswith("+"):
                field_name = sort_str[1:]
                arrow = Uniconst.ARROW_UP  # ▲ for ascending
            else:
                field_name = sort_str
                arrow = Uniconst.ARROW_UP

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
            self.search_mode_label.setText("")
            return

        # Map condition to user-friendly label
        mode_labels = {
            "and": "All terms (AND)",
            "or": "Any term (OR)",
            "exact": "Exact sentence",
            "id": "Video ID",
        }
        mode_label = mode_labels.get(search.cond, search.cond)
        self.search_mode_label.setText(f"Mode: {mode_label}")

        # Update search input if it doesn't match
        if self.search_input.text() != search.text:
            self.search_input.setText(search.text)

    def _update_grouping_display(self, context: VideoSearchContext):
        """Update the grouping info label with detailed information."""
        grouping = context.grouping
        if not grouping or not grouping.field:
            self.grouping_info.setText("No grouping")
            return

        # Build info lines
        lines = []

        # Field name (with property indicator)
        field_name = grouping.field.replace("_", " ").title()
        if grouping.is_property:
            lines.append(f"Field: {field_name} (property)")
        else:
            lines.append(f"Field: {field_name}")

        # Number of groups
        nb_groups = len(context.classifier_stats) if context.classifier_stats else 0
        lines.append(f"Groups: {nb_groups}")

        # Sorting info
        sort_labels = {"field": "by value", "count": "by count", "length": "by length"}
        sort_text = sort_labels.get(grouping.sorting, grouping.sorting)
        order = "desc" if grouping.reverse else "asc"
        lines.append(f"Sort: {sort_text} ({order})")

        # Singletons
        if not grouping.allow_singletons:
            lines.append("(no singletons)")

        self.grouping_info.setText("\n".join(lines))

    def _display_videos(self, videos: list[VideoPattern]):
        """Display the videos in the content area."""
        self._videos = videos

        if self._current_view == self.VIEW_GRID:
            self._display_grid_view(videos)
        else:
            self._display_list_view(videos)

    def _display_grid_view(self, videos: list[VideoPattern]):
        """Display videos in grid view."""
        # Clear existing video cards
        self._clear_video_cards()

        # Add video cards - FlowLayout handles positioning automatically
        for video in videos:
            card = VideoCard(video)
            card.clicked.connect(self._on_video_clicked)
            card.double_clicked.connect(self._on_video_double_clicked)
            card.context_menu_requested.connect(self._on_video_context_menu)
            card.selected = video.video_id in self._selected_video_ids
            self.video_flow.addWidget(card)
            self._video_cards.append(card)

    def _display_list_view(self, videos: list[VideoPattern]):
        """Display videos in list view with VideoListItem widgets."""
        # Clear existing list items
        self._clear_list_items()

        # Add video list items (insert before the stretch at the end)
        for i, video in enumerate(videos):
            item = VideoListItem(video)
            item.clicked.connect(self._on_video_clicked)
            item.double_clicked.connect(self._on_video_double_clicked)
            item.context_menu_requested.connect(self._on_video_context_menu)

            # Set selection state
            item.selected = video.video_id in self._selected_video_ids

            # Insert before the stretch (which is at the end)
            self.list_layout.insertWidget(i, item)
            self._video_list_items.append(item)

    def _clear_list_items(self):
        """Clear all video list items."""
        for item in self._video_list_items:
            self.list_layout.removeWidget(item)
            item.deleteLater()
        self._video_list_items.clear()

    def _clear_video_cards(self):
        """Clear all video cards from the grid."""
        for card in self._video_cards:
            self.video_flow.removeWidget(card)
            card.deleteLater()
        self._video_cards.clear()
        self._selected_video_id = None

    def _on_video_clicked(self, video_id: int, modifiers=None):
        """Handle video card click with optional modifier keys."""
        # Find clicked video index
        clicked_index = -1
        for i, video in enumerate(self._videos):
            if video.video_id == video_id:
                clicked_index = i
                break

        if modifiers is None:
            modifiers = Qt.KeyboardModifier.NoModifier

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+Click: Toggle selection
            if video_id in self._selected_video_ids:
                self._selected_video_ids.discard(video_id)
            else:
                self._selected_video_ids.add(video_id)
            self._last_clicked_index = clicked_index

        elif modifiers & Qt.KeyboardModifier.ShiftModifier:
            # Shift+Click: Range selection
            if self._last_clicked_index >= 0 and clicked_index >= 0:
                start_idx = min(self._last_clicked_index, clicked_index)
                end_idx = max(self._last_clicked_index, clicked_index)
                for i in range(start_idx, end_idx + 1):
                    if i < len(self._videos):
                        self._selected_video_ids.add(self._videos[i].video_id)
            else:
                self._selected_video_ids = {video_id}
                self._last_clicked_index = clicked_index

        else:
            # Normal click: Single selection
            self._selected_video_ids = {video_id}
            self._last_clicked_index = clicked_index

        # Update legacy single selection tracking
        self._selected_video_id = video_id
        self._update_selection_display()

    def _on_video_double_clicked(self, video_id: int):
        """Handle video card double-click (open video)."""
        if self.ctx.ops:
            self.ctx.ops.open_video(video_id)

    def _on_video_context_menu(self, video_id: int, pos):
        """Show context menu for a video."""
        menu = QMenu(self)

        menu.addAction("Open", lambda: self._open_video(video_id))
        menu.addAction("Open in VLC", lambda: self._open_in_vlc(video_id))
        menu.addAction("Open Folder", lambda: self._open_folder(video_id))
        menu.addSeparator()
        menu.addAction("Toggle Watched", lambda: self._toggle_watched(video_id))
        menu.addAction("Move to...", lambda: self._move_video(video_id))
        menu.addSeparator()
        menu.addAction("Properties...", lambda: self._show_properties(video_id))
        menu.addSeparator()
        menu.addAction("Delete from database", lambda: self._delete_video(video_id))

        menu.exec(pos)

    def _open_video(self, video_id: int):
        """Open a video with default player."""
        if self.ctx.ops:
            self.ctx.ops.open_video(video_id)

    def _open_in_vlc(self, video_id: int):
        """Open a video in VLC via server."""
        if self.ctx.api:
            self.ctx.api.open_from_server(video_id)

    def _open_folder(self, video_id: int):
        """Open the folder containing the video."""
        if self.ctx.api:
            self.ctx.api.open_containing_folder(video_id)

    def _toggle_watched(self, video_id: int):
        """Toggle the watched status of a video."""
        if self.ctx.ops:
            self.ctx.ops.toggle_watched(video_id)
            self.refresh()

    def _move_video(self, video_id: int):
        """Move a video file to a different folder."""
        if not self.ctx.database:
            return

        # Get database folders for initial directory
        folders = list(self.ctx.database.get_folders())
        initial_dir = str(folders[0]) if folders else ""

        # Show folder selection dialog
        directory = QFileDialog.getExistingDirectory(
            self, "Move Video To", initial_dir, QFileDialog.Option.ShowDirsOnly
        )

        if not directory:
            return

        # Confirm the move
        videos = self.ctx.database.get_videos(where={"video_id": video_id})
        if not videos:
            return
        video = videos[0]

        reply = QMessageBox.question(
            self,
            "Move Video",
            f"Move '{video.title}' to:\n{directory}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Show home page and start the move operation
            self.long_operation_requested.emit()
            self.ctx.move_video_file(video_id, directory)

    def _show_properties(self, video_id: int):
        """Show properties dialog for a video."""
        if not self.ctx.database:
            return

        videos = self.ctx.database.get_videos(where={"video_id": video_id})
        if not videos:
            return
        video = videos[0]

        prop_types = self.ctx.database.get_prop_types()
        dialog = VideoPropertiesDialog(video, prop_types, self.ctx.database, self)
        if dialog.exec():
            # Refresh to show any property changes
            self.refresh()

    def _delete_video(self, video_id: int):
        """Delete a single video from the database (with confirmation)."""
        if not self.ctx.database:
            return

        videos = self.ctx.database.get_videos(where={"video_id": video_id})
        if not videos:
            return
        video = videos[0]

        reply = QMessageBox.question(
            self,
            "Delete Video",
            f"Delete '{video.title}' from the database?\n\n"
            "(The file will NOT be deleted from disk)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.ctx.database:
                self.ctx.database.video_entry_del(video_id)
                self.refresh()

    def _on_batch_edit(self):
        """Open batch edit dialog for selected videos."""
        if not self._selected_video_ids or not self.ctx.database:
            return

        prop_types = self.ctx.database.get_prop_types()
        if not prop_types:
            QMessageBox.information(
                self,
                "No Properties",
                "No custom properties defined.\n"
                "Create properties in the Properties page first.",
            )
            return

        from pysaurus.interface.pyside6.dialogs.batch_edit_dialog import BatchEditDialog

        video_ids = list(self._selected_video_ids)
        dialog = BatchEditDialog(video_ids, prop_types, self.ctx.database, self)
        if dialog.exec():
            self.refresh()

    def _on_view_changed(self, index: int):
        """Handle view mode change."""
        self._current_view = index
        self.view_stack.setCurrentIndex(index)
        # Re-display current videos in new view
        if self._videos:
            self._display_videos(self._videos)

    def _on_page_size_changed(self, text: str):
        """Handle page size change."""
        self.page_size = int(text)
        self.page_number = 0
        self.refresh()

    def _on_edit_sources(self):
        """Handle edit sources button."""
        # Get current sources from provider
        current_sources = None
        if self.ctx.provider:
            state = self.ctx.provider.get_current_state(1, 0)
            current_sources = state.sources if hasattr(state, "sources") else None

        dialog = SourcesDialog(current_sources, self)
        if dialog.exec():
            sources = dialog.get_sources()
            if self.ctx.provider:
                self.ctx.provider.set_sources(sources)
                self.page_number = 0
                self.refresh()

    def _on_set_grouping(self):
        """Handle set grouping button."""
        # Get current grouping
        current_grouping = None
        if self.ctx.provider:
            state = self.ctx.provider.get_current_state(1, 0)
            if state.grouping:
                current_grouping = {
                    "field": state.grouping.field,
                    "is_property": state.grouping.is_property,
                    "sorting": state.grouping.sorting,
                    "reverse": state.grouping.reverse,
                    "allow_singletons": state.grouping.allow_singletons,
                }

        # Get property types
        prop_types = self.ctx.database.get_prop_types() if self.ctx.database else []

        dialog = GroupingDialog(prop_types, current_grouping, self)
        if dialog.exec():
            grouping = dialog.get_grouping()
            if self.ctx.provider:
                if grouping is None:
                    # Clear grouping
                    self.ctx.provider.set_groups(None)
                else:
                    self.ctx.provider.set_groups(
                        field=grouping["field"],
                        is_property=grouping["is_property"],
                        sorting=grouping["sorting"],
                        reverse=grouping["reverse"],
                        allow_singletons=grouping["allow_singletons"],
                    )
                self.page_number = 0
                self.refresh()

    def _on_search(self):
        """Handle search on Enter key."""
        self._do_search("and")

    def _do_search(self, mode: str):
        """Perform search with given mode."""
        query = self.search_input.text().strip()
        if query and self.ctx.provider:
            self.ctx.provider.set_search(query, mode)
            self.page_number = 0
            self.refresh()

    def _clear_search(self):
        """Clear the search."""
        self.search_input.clear()
        if self.ctx.provider:
            self.ctx.provider.set_search("", "and")
            self.page_number = 0
            self.refresh()

    def _clear_sources(self):
        """Reset sources to default."""
        if self.ctx.provider:
            self.ctx.provider.set_sources(None)
            self.page_number = 0
            self.refresh()

    def _clear_grouping(self):
        """Remove grouping."""
        if self.ctx.provider:
            self.ctx.provider.set_groups(None)
            self.page_number = 0
            self.refresh()

    def _clear_sorting(self):
        """Reset sorting to default."""
        if self.ctx.provider:
            self.ctx.provider.set_sort(None)
            self.page_number = 0
            self.refresh()

    def _on_set_sorting(self):
        """Handle set sorting button."""
        # Get current sorting
        current_sorting = None
        if self.ctx.provider:
            state = self.ctx.provider.get_current_state(1, 0)
            if state.sorting:
                video_sorting = state.get_video_sorting()
                current_sorting = list(video_sorting)  # list of (field, reverse) tuples

        dialog = SortingDialog(current_sorting, self)
        if dialog.exec():
            sorting_tuples = dialog.get_sorting()
            if self.ctx.provider:
                # Convert (field, reverse) tuples to "-field" or "+field" strings
                sorting_strings = [
                    f"-{field}" if reverse else f"+{field}"
                    for field, reverse in sorting_tuples
                ]
                self.ctx.provider.set_sort(sorting_strings)
                self.page_number = 0
                self.refresh()

    def _on_random_video(self):
        """Open a random video and configure search to show it."""
        if self.ctx.provider:
            # Get a random video ID and configure search with it
            video_id = self.ctx.provider.get_random_found_video_id()
            if video_id:
                # Reset grouping and configure search with video ID
                self.ctx.provider.reset_parameters(
                    self.ctx.provider.LAYER_GROUPING,
                    self.ctx.provider.LAYER_CLASSIFIER,
                    self.ctx.provider.LAYER_GROUP,
                )
                self.ctx.provider.set_search(str(video_id), "id")
                # Update search input to show the video ID
                self.search_input.setText(str(video_id))
                # Open the video
                if self.ctx.ops:
                    self.ctx.ops.open_video(video_id)
                # Refresh display
                self.page_number = 0
                self.refresh()

    def _on_find_similar(self):
        """Find similar videos."""
        # Emit signal to show home page
        self.long_operation_requested.emit()
        # Start the similarity search
        self.ctx.find_similar_videos()

    def _on_back_to_databases(self):
        """Navigate back to databases page."""
        main_window = self.window()
        if hasattr(main_window, "show_databases_page"):
            main_window.show_databases_page()

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

    def _on_group_selected(self, index: int):
        """Handle group selection from combo box."""
        if index >= 0 and index != self._current_group_index:
            self._select_group(index)

    def _select_group(self, index: int):
        """Select a group by index."""
        if not self._group_stats or index < 0 or index >= len(self._group_stats):
            return

        if self.ctx.provider:
            self.ctx.provider.set_group(index)
            self.page_number = 0
            self.refresh()

    def _go_first(self):
        """Go to first page."""
        self.page_number = 0
        self.refresh()

    def _go_prev(self):
        """Go to previous page."""
        if self.page_number > 0:
            self.page_number -= 1
            self.refresh()

    def _go_next(self):
        """Go to next page."""
        self.page_number += 1
        self.refresh()

    def _go_last(self):
        """Go to last page."""
        if self.ctx.provider:
            context = self.ctx.get_videos(self.page_size, 0)
            self.page_number = max(0, context.nb_pages - 1)
            self.refresh()
