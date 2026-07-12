"""Install Qt's own built-in translations for the current language.

Pysaurus's strings go through ``say()``; but Qt's built-in widget strings —
``QDialogButtonBox`` Ok/Cancel/Close, the default buttons of a static
``QMessageBox``, text-field context menus (Copy, Select All)... — are
translated by Qt itself from the ``qtbase_<code>.qm`` catalogs shipped with
PySide6. This installs the matching one and swaps it on language change.

Complements ``say()`` (Qt owns its widget strings, ``say()`` owns app strings);
it is not a competing app-string catalog.
"""

from PySide6.QtCore import QLibraryInfo, QTranslator
from PySide6.QtWidgets import QApplication


class QtStandardTranslations:
    """Owns the QTranslator(s) installed on the QApplication for one language."""

    def __init__(self):
        self._translators: list[QTranslator] = []

    def apply(self, code: str) -> None:
        """Swap to the Qt catalog for ``code`` (an ISO 639-1 language code).

        Removing the previous translator reverts to Qt's source English, so a
        missing ``qtbase_<code>.qm`` (e.g. for English itself) is harmless.
        """
        app = QApplication.instance()
        if app is None:  # e.g. headless context with no QApplication
            return
        for translator in self._translators:
            app.removeTranslator(translator)
        self._translators.clear()
        directory = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        translator = QTranslator(app)
        if translator.load(f"qtbase_{code}", directory):
            app.installTranslator(translator)
            self._translators.append(translator)
