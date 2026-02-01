"""
Home page showing loading progress.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor
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

from pysaurus.core.notifications import Notification
from pysaurus.interface.pyside6.app_context import AppContext


class JobProgressWidget(QFrame):
    """Widget displaying progress for a single job."""

    def __init__(self, name: str, total: int, title: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.total = total
        self.title = title
        self._channels: dict[str, int] = {}

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
        # Style the progress bar
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

    @property
    def current(self) -> int:
        return sum(self._channels.values())

    def update_progress(self, channel: str, step: int, title: str | None = None):
        """Update progress for a channel."""
        self._channels[channel] = step
        current = self.current

        self.progress_bar.setValue(current)

        if self.total > 0:
            percent = round(current * 100 / self.total)
            self.percent_label.setText(f"{percent}%")

        if title:
            self.title_label.setText(title)

    def is_done(self) -> bool:
        return self.current >= self.total


class HomePage(QWidget):
    """
    Page showing database loading progress.

    Displays:
    - Active job progress bars
    - Activity log with notifications
    - Cancel button
    - Continue button (enabled when ready)
    """

    # Signal emitted when user clicks Continue
    continue_requested = Signal()

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._jobs: dict[str, JobProgressWidget] = {}
        self._is_ready = False
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)

        # Title
        self.title_label = QLabel("Loading Database...")
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
        # Style text with palette and font
        palette = self.global_progress.palette()
        palette.setColor(QPalette.ColorRole.Text, QColor("white"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
        self.global_progress.setPalette(palette)
        font = self.global_progress.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() - 1)
        self.global_progress.setFont(font)
        self.global_progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.global_progress)

        # Jobs container (scroll area for multiple progress bars)
        jobs_group = QFrame()
        jobs_group.setFrameStyle(QFrame.Shape.StyledPanel)
        self.jobs_layout = QVBoxLayout(jobs_group)
        self.jobs_layout.setContentsMargins(5, 5, 5, 5)
        self.jobs_layout.setSpacing(5)

        # Add stretch at the bottom to keep jobs at top
        self.jobs_layout.addStretch()

        jobs_scroll = QScrollArea()
        jobs_scroll.setWidget(jobs_group)
        jobs_scroll.setWidgetResizable(True)
        jobs_scroll.setMinimumHeight(150)
        jobs_scroll.setMaximumHeight(200)
        layout.addWidget(jobs_scroll)

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

        log_scroll = QScrollArea()
        log_scroll.setWidget(self.log_container)
        log_scroll.setWidgetResizable(True)
        self._log_scroll = log_scroll
        layout.addWidget(log_scroll, stretch=1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_continue = QPushButton("Continue →")
        self.btn_continue.setEnabled(False)
        self.btn_continue.setMinimumWidth(120)
        self.btn_continue.setStyleSheet(
            "QPushButton:enabled { background-color: #4CAF50; color: white; font-weight: bold; }"
        )
        self.btn_continue.clicked.connect(self._on_continue)
        btn_layout.addWidget(self.btn_continue)

        layout.addLayout(btn_layout)

    def _connect_signals(self):
        """Connect signals from context."""
        self.ctx.notification_received.connect(self._on_notification)
        self.ctx.profiling_started.connect(self._on_profiling_started)
        self.ctx.profiling_ended.connect(self._on_profiling_ended)
        self.ctx.job_started.connect(self._on_job_started)
        self.ctx.job_progress.connect(self._on_job_progress)
        self.ctx.operation_done.connect(self._on_operation_done)
        self.ctx.operation_cancelled.connect(self._on_operation_cancelled)
        self.ctx.database_ready.connect(self._on_database_ready)

    def _on_notification(self, notification: Notification):
        """Handle notifications (for logging)."""
        # Skip JobToDo and JobStep - they're handled separately
        from pysaurus.core.job_notifications import JobStep, JobToDo

        if isinstance(notification, (JobToDo, JobStep)):
            return

        # Log the notification
        message = str(notification)
        if message:
            self._add_log_entry(message)

    def _on_profiling_started(self, name: str):
        """Handle profiling start."""
        self.task_label.setText(name)

    def _on_profiling_ended(self, name: str, time: str):
        """Handle profiling end."""
        self._add_log_entry(f"✓ {name} ({time})", bold=True)

    def _on_job_started(self, name: str, total: int, title: str):
        """Handle job start - create progress bar."""
        # Skip jobs with 0 total (nothing to do)
        if total <= 0:
            return

        if name in self._jobs:
            # Remove existing job widget
            self._remove_job(name)

        # Create new progress widget
        widget = JobProgressWidget(name, total, title)
        self._jobs[name] = widget

        # Insert before the stretch
        self.jobs_layout.insertWidget(self.jobs_layout.count() - 1, widget)

    def _on_job_progress(
        self, name: str, channel: str, step: int, total: int, title: str
    ):
        """Handle job progress update."""
        # Skip jobs with 0 total (nothing to do)
        if total <= 0:
            return

        if name not in self._jobs:
            # Job not started yet, create it
            self._on_job_started(name, total, title)

        widget = self._jobs.get(name)
        if widget:
            widget.update_progress(channel, step, title if title else None)

            # Remove completed jobs
            if widget.is_done():
                self._remove_job(name)

    def _remove_job(self, name: str):
        """Remove a job widget."""
        if name in self._jobs:
            widget = self._jobs.pop(name)
            self.jobs_layout.removeWidget(widget)
            widget.deleteLater()

    def _on_operation_done(self):
        """Handle operation done."""
        self._add_log_entry("Done!", bold=True, color="green")
        self._clear_jobs()

    def _on_operation_cancelled(self):
        """Handle operation cancelled."""
        self._add_log_entry("Cancelled.", bold=True, color="orange")
        self._clear_jobs()

    def _clear_jobs(self):
        """Clear all job widgets."""
        for name in list(self._jobs.keys()):
            self._remove_job(name)

    def _add_log_entry(self, text: str, bold: bool = False, color: str = None):
        """Add an entry to the activity log."""
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

        # Auto-scroll to bottom
        self._log_scroll.verticalScrollBar().setValue(
            self._log_scroll.verticalScrollBar().maximum()
        )

    def _clear_log(self):
        """Clear the activity log."""
        # Remove all widgets except the stretch
        while self.log_layout.count() > 1:
            item = self.log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.ctx.cancel_operation()

    def _on_database_ready(self):
        """Handle database ready - enable continue button."""
        self._is_ready = True
        self._clear_jobs()  # Clear any remaining progress bars
        self.btn_continue.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.title_label.setText("Database Ready!")
        self.task_label.setText("Click 'Continue' to browse videos")
        self.global_progress.setRange(0, 1)
        self.global_progress.setValue(1)

    def _on_continue(self):
        """Handle continue button click."""
        self.continue_requested.emit()

    def reset(self):
        """Reset the page for a new loading operation."""
        self._clear_log()
        self._clear_jobs()
        self._is_ready = False
        self.task_label.setText("")
        self.title_label.setText("Loading Database...")
        self.btn_continue.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.global_progress.setRange(0, 0)  # Indeterminate
