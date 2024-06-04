from PySide6.QtWidgets import QMessageBox

from pysaurus.application.exceptions import PysaurusError


class QtsAlerter:
    __slots__ = ("widget", "description", "exc_types")

    def __init__(self, widget, description="", exc_types=(Exception,)):
        self.widget = widget
        self.description = description
        self.exc_types = exc_types

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, self.exc_types):
            if self.description:
                title = f"{self.description} ({exc_type.__name__})"
            else:
                title = exc_type.__name__
            QMessageBox.critical(self.widget, title, str(exc_val))
            return True


class QtsAppAlerter(QtsAlerter):
    __slots__ = ()

    def __init__(self, widget, description=""):
        super().__init__(widget, description, (PysaurusError, OSError))
