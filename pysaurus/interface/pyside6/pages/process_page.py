"""
Process page for displaying operation progress.

Each ProcessPage creates its own NotificationCollector to handle
notifications independently, avoiding state conflicts between operations.
"""

from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.job_notifications import (
    JobProgressDisplay,
    JobStep,
    JobToDo,
    NotificationCollector,
)
from pysaurus.core.notifications import End, Notification, ProfilingEnd


class ProcessJobProgress(JobProgressDisplay):
    """Job progress display that updates a Qt widget."""

    __slots__ = ("widget",)

    def __init__(self, job_to_do: JobToDo, widget: "JobProgressWidget"):
        self.widget = widget
        super().__init__(job_to_do)

    def _display(self, step: int):
        """Update the Qt widget with current progress."""
        self.widget.set_progress(step)


class JobProgressWidget(QFrame):
    """Widget displaying progress for a single job."""

    def __init__(self, name: str, total: int, title: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.total = total
        self.title = title

        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Title label
        self.title_label = QLabel(self.title or self.name)
        self.title_label.setMinimumWidth(200)
        self.title_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self.title_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.total)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
        """)
        # Style text with palette and font
        palette = self.progress_bar.palette()
        palette.setColor(QPalette.ColorRole.Text, QColor("white"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
        self.progress_bar.setPalette(palette)
        font = self.progress_bar.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() - 1)
        self.progress_bar.setFont(font)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)

        # Percentage label
        self.percent_label = QLabel("0%")
        self.percent_label.setMinimumWidth(50)
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.percent_label)

    def set_progress(self, current: int):
        """Update progress display."""
        self.progress_bar.setValue(current)
        if self.total > 0:
            percent = round(current * 100 / self.total)
            self.percent_label.setText(f"{percent}%")


class ProcessNotificationCollector(NotificationCollector):
    """Notification collector that updates ProcessPage UI."""

    __slots__ = ("page",)

    def __init__(self, page: "ProcessPage"):
        super().__init__()
        self.page = page

    def _display_notification(self, notification: Notification):
        """Display a notification in the log."""
        self.page.add_log_entry(str(notification))

    def _new_progress(self, job_to_do: JobToDo) -> JobProgressDisplay:
        """Create a new progress widget for the job."""
        widget = self.page.create_job_widget(job_to_do)
        return ProcessJobProgress(job_to_do, widget)


class ProcessPage(QWidget):
    """
    Page displaying progress for a single operation.

    Creates its own NotificationCollector to handle notifications
    independently from other operations.

    When the operation ends (End notification), displays a Continue button
    that triggers the callback to navigate to the next page.
    """

    # Signal emitted when user clicks Continue
    continue_clicked = Signal(object)  # Emits the End notification

    def __init__(
        self,
        title: str,
        callback: Callable[[End], None] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.title = title
        self.callback = callback
        self._job_widgets: dict[str, JobProgressWidget] = {}
        self._end_notification: End | None = None

        # Create our own notification collector
        self.collector = ProcessNotificationCollector(self)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)

        # Title
        self.title_label = QLabel(f"{self.title}...")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; padding: 10px;"
        )
        layout.addWidget(self.title_label)

        # Current task label
        self.task_label = QLabel("")
        self.task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.task_label.setStyleSheet("font-size: 14px; color: #555; padding: 5px;")
        layout.addWidget(self.task_label)

        # Global progress bar (indeterminate)
        self.global_progress = QProgressBar()
        self.global_progress.setRange(0, 0)  # Indeterminate
        self.global_progress.setFixedHeight(20)
        self.global_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.global_progress)

        # Jobs container (scroll area for multiple progress bars)
        jobs_group = QFrame()
        jobs_group.setFrameStyle(QFrame.Shape.StyledPanel)
        self.jobs_layout = QVBoxLayout(jobs_group)
        self.jobs_layout.setContentsMargins(5, 5, 5, 5)
        self.jobs_layout.setSpacing(5)
        self.jobs_layout.addStretch()

        self.jobs_scroll = QScrollArea()
        self.jobs_scroll.setWidget(jobs_group)
        self.jobs_scroll.setWidgetResizable(True)
        self.jobs_scroll.setMinimumHeight(150)
        self.jobs_scroll.setMaximumHeight(200)
        # Auto-scroll when content changes
        self.jobs_scroll.verticalScrollBar().rangeChanged.connect(
            lambda _, max_val: self.jobs_scroll.verticalScrollBar().setValue(max_val)
        )
        layout.addWidget(self.jobs_scroll)

        # Activity log header
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("Activity Log:"))
        log_header.addStretch()

        self.btn_clear_log = QPushButton("Clear")
        self.btn_clear_log.setFixedWidth(60)
        self.btn_clear_log.clicked.connect(self._clear_log)
        log_header.addWidget(self.btn_clear_log)

        layout.addLayout(log_header)

        # Activity log (scroll area)
        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setContentsMargins(5, 5, 5, 5)
        self.log_layout.setSpacing(2)
        self.log_layout.addStretch()

        self.log_scroll = QScrollArea()
        self.log_scroll.setWidget(self.log_container)
        self.log_scroll.setWidgetResizable(True)
        # Auto-scroll when content changes
        self.log_scroll.verticalScrollBar().rangeChanged.connect(
            lambda _, max_val: self.log_scroll.verticalScrollBar().setValue(max_val)
        )
        layout.addWidget(self.log_scroll, stretch=1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_continue = QPushButton("Continue")
        self.btn_continue.setEnabled(False)
        self.btn_continue.setMinimumWidth(120)
        self.btn_continue.setStyleSheet(
            "QPushButton:enabled { background-color: #4CAF50; color: white; font-weight: bold; }"
        )
        self.btn_continue.clicked.connect(self._on_continue)
        btn_layout.addWidget(self.btn_continue)

        layout.addLayout(btn_layout)

    def on_notification(self, notification: Notification):
        """
        Handle a notification.

        This method should be called for each notification received.
        It delegates to the collector for proper handling.
        """
        # Collect the notification (handles jobs, profiling, etc.)
        self.collector.collect(notification)

        # Handle specific notification types for UI updates
        if isinstance(notification, End):
            self._on_end(notification)
        elif isinstance(notification, ProfilingEnd):
            self.add_log_entry(f"✓ {notification.name} ({notification.time})", bold=True)

    def _on_end(self, notification: End):
        """Handle end notification - show Continue button."""
        self._end_notification = notification
        self.title_label.setText(f"{self.title} - {notification}")
        self.task_label.setText("Click 'Continue' to proceed")
        self.global_progress.setRange(0, 1)
        self.global_progress.setValue(1)
        self.btn_continue.setEnabled(True)
        # Keep progress bars visible so user can see what happened

    def _on_continue(self):
        """Handle Continue button click."""
        if self.callback and self._end_notification:
            self.callback(self._end_notification)
        self.continue_clicked.emit(self._end_notification)

    def create_job_widget(self, job_to_do: JobToDo) -> JobProgressWidget:
        """Create and add a job progress widget."""
        name = job_to_do.name

        # Remove existing widget if any
        if name in self._job_widgets:
            self._remove_job_widget(name)

        # Create new widget
        widget = JobProgressWidget(name, job_to_do.total, job_to_do.title)
        self._job_widgets[name] = widget

        # Insert before the stretch
        self.jobs_layout.insertWidget(self.jobs_layout.count() - 1, widget)

        return widget

    def _remove_job_widget(self, name: str):
        """Remove a job widget."""
        if name in self._job_widgets:
            widget = self._job_widgets.pop(name)
            self.jobs_layout.removeWidget(widget)
            widget.deleteLater()

    def add_log_entry(self, text: str, bold: bool = False, color: str = None):
        """Add an entry to the activity log."""
        if not text:
            return

        label = QLabel(text)
        label.setWordWrap(True)

        style = ""
        if bold:
            style += "font-weight: bold; "
        if color:
            style += f"color: {color}; "
        if style:
            label.setStyleSheet(style)

        # Insert before the stretch
        self.log_layout.insertWidget(self.log_layout.count() - 1, label)

    def _clear_log(self):
        """Clear the activity log."""
        while self.log_layout.count() > 1:
            item = self.log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
