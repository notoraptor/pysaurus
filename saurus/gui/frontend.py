import sys
import threading
from multiprocessing import freeze_support

from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
from PyQt5.QtWidgets import QApplication

from pysaurus.core.modules import System

freeze_support()


def generate_except_hook(qapp):
    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)
        qapp.exit(1)

    return except_hook


def generate_thread_except_hook(qapp):
    def thread_except_hook(arg):
        print("[Qt] Error occurring in thread:", arg.thread.name, file=sys.stderr)
        sys.__excepthook__(arg.exc_type, arg.exc_value, arg.exc_traceback)
        qapp.exit(1)

    return thread_except_hook


class CustomPage(QWebEnginePage):
    LevelType = QWebEnginePage.JavaScriptConsoleMessageLevel
    LEVEL = {
        LevelType.InfoMessageLevel: "info",
        LevelType.WarningMessageLevel: "warning",
        LevelType.ErrorMessageLevel: "error",
    }

    def javaScriptConsoleMessage(
        self, level: LevelType, message: str, line_number: int, source_id: str
    ):
        file = sys.stdout if level == self.LevelType.InfoMessageLevel else sys.stderr
        print(f"[JS:{self.LEVEL[level]}] {source_id}", file=file)
        print(f"{line_number}:{message}", file=file)


class View(QWebEngineView):
    def __init__(self, html):
        super().__init__()

        # setup page
        self.web_page = CustomPage()
        self.web_page.setHtml(
            f"""
<html>
<head>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
</head>
<body>
{html}
<script>
console.log('hello');
</script>
</body>
</html>
""".strip()
        )
        self.setPage(self.web_page)

    def set_view(self, app: QApplication):
        # Set geometry.
        screen_rect = app.desktop().screen().rect()
        screen_center = screen_rect.center()
        width = (7 * screen_rect.width()) // 10
        height = (2 * screen_rect.height()) // 3
        x = screen_center.x() - width // 2
        y = screen_center.y() - height // 2
        print(f"Window: size {width} x {height}, position ({x}; {y})", file=sys.stderr)
        self.setGeometry(x, y, width, height)
        # Set zoom.
        if System.is_windows():
            # view.setZoomFactor(1.8)
            screen_height = screen_rect.height()
            base_height = 1080
            if screen_height > base_height:
                scale = (screen_height / base_height) * 0.9
                print("Scale", scale)
                self.setZoomFactor(scale)


def gui(html):
    # Initialize.
    app = QApplication.instance() or QApplication(sys.argv)
    sys.excepthook = generate_except_hook(app)
    threading.excepthook = generate_thread_except_hook(app)
    view = View(html)
    view.set_view(app)
    # Display.
    view.show()
    return app.exec_()
