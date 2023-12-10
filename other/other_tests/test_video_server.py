from flask import Flask, send_file

from pysaurus.database.db_video_server import ServerLauncher

TEST_PATH = (
    r"\\?\H:\donnees\torrents\anime\vostfr\[Elecman] Ikki Tousen Integral S1-S7 [BDRIP "
    r"CUSTOM][1080p x265 10bits Multi,Vostfr]\[Elecman] Ikki Tousen S2 Dragon "
    r"Destiny [BDRIP CUSTOM][1080p x265 10bits Multi]V2\[Elecman] Ikki Tousen "
    r"Dragon Destiny E01 [BDRIP CUSTOM][1080p x265 10bits Multi].mkv"
)


def main_flask():
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "Pysaurus Video Server"

    @app.route("/video", methods=["GET"])
    def video():
        return send_file(TEST_PATH)

    app.run()


def main_werkzeug():
    print("PATH", len(TEST_PATH), TEST_PATH)
    launcher = ServerLauncher(None)
    launcher.start()
    input("Type something:")
    launcher.stop()


if __name__ == "__main__":
    # main_flask()
    main_werkzeug()
