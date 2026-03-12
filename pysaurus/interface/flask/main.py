"""Entry point for the Flask interface."""

import logging
import threading
import webbrowser

from pysaurus.application.application import Application
from pysaurus.core.informer import Information
from pysaurus.interface.flask.app import create_app
from pysaurus.interface.flask.context import FlaskContext

logger = logging.getLogger(__name__)

PORT = 5000


def _init():
    """Create Application, FlaskContext and Flask app."""
    application = Application(notifier=Information.notifier())
    FlaskContext.instance = FlaskContext(application)
    return create_app()


def main():
    """Launch Flask server and open the browser."""
    with Information():
        app = _init()
        webbrowser.open(f"http://127.0.0.1:{PORT}")
        app.run(host="127.0.0.1", port=PORT, debug=False)


def main_desktop():
    """Launch Flask server in a background thread + pywebview window."""
    import webview

    with Information():
        app = _init()

        server = threading.Thread(
            target=app.run,
            kwargs={"host": "127.0.0.1", "port": PORT, "debug": False},
            daemon=True,
        )
        server.start()

        webview.create_window("Pysaurus", f"http://127.0.0.1:{PORT}")
        webview.start()
        # webview.start() blocks until the window is closed.
        # The daemon server thread is killed automatically on exit.
        # If a long operation is running, wait for it to finish cleanly.
        if FlaskContext.instance:
            FlaskContext.instance.wait_for_operation(timeout=5)


if __name__ == "__main__":
    main_desktop()
