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
        self.port = 5000
        self.server = make_server(self.hostname, self.port, appl, threaded=True)
        self.ctx = appl.app_context()
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
        filename = database.get_video_filename(video_id)
        logger.info(f"Found video: {filename}")
        return send_file(filename.path)
