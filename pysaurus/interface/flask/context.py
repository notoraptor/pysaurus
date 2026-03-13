"""Flask application context — facade to Application/Database layers."""

import logging
import threading

from pysaurus.application.application import Application
from pysaurus.core.informer import Information
from pysaurus.core.job_notifications import JobStep, JobToDo
from pysaurus.core.notifications import End, Notification
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.database_algorithms import DatabaseAlgorithms
from pysaurus.database.database_operations import DatabaseOperations

logger = logging.getLogger(__name__)


class OperationState:
    """Shared state for a long-running operation, read by polling."""

    __slots__ = ("running", "done", "percent", "message", "redirect_url", "error")

    def __init__(self, redirect_url="/videos"):
        self.running = False
        self.done = False
        self.percent = 0
        self.message = ""
        self.redirect_url = redirect_url
        self.error = None


class FlaskContext:
    """Facade for accessing backend layers from Flask routes.

    Stored as a class attribute (FlaskContext.instance) rather than a module
    singleton, so it survives Flask's development reloader re-importing the module.
    """

    instance: "FlaskContext | None" = None

    def __init__(self, application: Application):
        self.application = application
        self._database: AbstractDatabase | None = None
        self._operation = OperationState()
        self._operation_thread: threading.Thread | None = None
        Information.handle_with(self._on_notification)

    @property
    def operation_running(self) -> bool:
        return self._operation.running

    @property
    def operation_state(self) -> OperationState:
        return self._operation

    @property
    def database(self) -> AbstractDatabase | None:
        return self._database

    @property
    def ops(self) -> DatabaseOperations | None:
        return self._database.ops if self._database else None

    @property
    def algos(self) -> DatabaseAlgorithms | None:
        return self._database.algos if self._database else None

    # Database management

    def get_database_names(self) -> list[str]:
        return self.application.get_database_names()

    def get_database_name(self) -> str:
        return self._database.get_name() if self._database else ""

    def open_database(self, name: str) -> None:
        self._database = self.application.open_database_from_name(name, update=False)

    def close_database(self) -> None:
        self._database = None

    def create_database(self, name: str, folders: list[str]) -> None:
        from pysaurus.core.absolute_path import AbsolutePath

        abs_folders = [AbsolutePath(f) for f in folders if f.strip()]
        self._database = self.application.new_database(name, abs_folders, update=False)

    def delete_database(self, name: str) -> None:
        self.application.delete_database_from_name(name)

    def rename_database(self, new_name: str) -> None:
        if self._database:
            old_path = self._database.get_database_folder()
            self._database.rename(new_name)
            new_path = self._database.get_database_folder()
            if old_path in self.application.databases:
                del self.application.databases[old_path]
                self.application.databases[new_path] = self._database

    # Video operations

    def get_video(self, video_id: int):
        """Return a single VideoPattern or None."""
        videos = self._database.get_videos(where={"video_id": video_id})
        return videos[0] if videos else None

    def get_thumbnails_base64(self, video_ids: list[int]) -> dict[int, str]:
        """Return {video_id: "data:image/jpeg;base64,..."} for given IDs.

        Fetches all thumbnails in a single SQL query and encodes them
        as data URIs for direct embedding in <img src="...">.
        """
        from base64 import b64encode

        from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection

        db = self._database
        if not isinstance(db, PysaurusCollection) or not video_ids:
            return {}
        placeholders = ",".join("?" * len(video_ids))
        rows = db.db.query_all(
            f"SELECT video_id, thumbnail FROM video_thumbnail "
            f"WHERE video_id IN ({placeholders})",
            video_ids,
        )
        return {
            row[0]: f"data:image/jpeg;base64,{b64encode(row[1]).decode()}"
            for row in rows
            if row[1]
        }

    def get_prop_types(self) -> list[dict]:
        return self._database.get_prop_types() if self._database else []

    # Long operations

    def start_operation(self, callable_, redirect_url="/videos"):
        """Launch a long operation in a secondary thread."""
        if self._operation.running:
            return
        self._operation = OperationState(redirect_url)
        self._operation.running = True

        def run():
            try:
                callable_()
            except Exception as exc:
                logger.exception("Long operation failed")
                self._operation.error = str(exc)
            finally:
                self._operation.done = True
                self._operation.running = False

        self._operation_thread = threading.Thread(target=run, daemon=True)
        self._operation_thread.start()

    def wait_for_operation(self, timeout: float = 5) -> None:
        """Wait for the current operation thread to finish (if any)."""
        thread = self._operation_thread
        if thread is not None and thread.is_alive():
            logger.info("Waiting for running operation to finish...")
            thread.join(timeout=timeout)

    def _on_notification(self, notification: Notification):
        """Notification callback (called from Information monitor thread)."""
        op = self._operation
        if not op.running:
            return
        if isinstance(notification, JobToDo):
            op.message = notification.title or notification.name
            op.percent = 0
        elif isinstance(notification, JobStep):
            if notification.total > 0:
                op.percent = int(notification.step * 100 / notification.total)
            if notification.title:
                op.message = notification.title
        elif isinstance(notification, End):
            op.percent = 100
