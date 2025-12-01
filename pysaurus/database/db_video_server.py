import logging
import threading

from flask import Flask, send_file
from werkzeug.serving import make_server

logger = logging.getLogger(__name__)


class _ServerThread(threading.Thread):
    def __init__(self, appl):
        # Make thread a daemon to be sure it is closed if sys.exit is called.
        # (2022/12/29) https://stackoverflow.com/a/38805873
        super().__init__(daemon=True)
        self.hostname = "127.0.0.1"
        self.port = 0  # Set port to 0 so that system chooses a port dynamically
        self.server = make_server(self.hostname, self.port, appl, threaded=True)
        # Save back opened port
        self.port = self.server.server_port

        # Create an application context for this thread
        # App context is crucial for Flask to work properly in a separate thread
        # It provides access to app-wide variables and ensures proper request isolation
        self.ctx = appl.app_context()

        # Push the context onto the context stack
        # This makes the context active for the current thread
        # Without this, Flask would not know which context to use for handling requests
        # in this thread, and operations like accessing current_app, request, or
        # session would fail
        self.ctx.push()

    def run(self):
        logger.info("starting server ...")
        self.server.serve_forever()

    def shutdown(self):
        logger.info("Closing server ...")
        self.server.shutdown()
        logger.info("Server closed.")


class ServerLauncher:
    def __init__(self, database_getter):
        self.db_getter = database_getter
        self.application = Flask(__name__)
        self.application.route("/")(self._home)
        self.application.route("/video/<video_id>")(self._video)
        self.server_thread = _ServerThread(self.application)

    def start(self):
        self.server_thread.start()
        logger.info("server started")

    def stop(self):
        self.server_thread.shutdown()

    @classmethod
    def _home(cls):
        return "Pysaurus Video Server"

    def _video(self, video_id):
        # TODO An error here does not stop the program.
        video_id = int(video_id)
        logger.info(f"Required video ID {video_id}")
        database = self.db_getter()
        filename = database.ops.get_video_filename(video_id)
        logger.info(f"Found video: {filename}")
        return send_file(filename.path)
