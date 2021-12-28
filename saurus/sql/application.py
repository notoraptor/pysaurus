from pathlib import Path

from pysaurus.core.components import AbsolutePath
from saurus.language import say
from saurus.sql.video_database import VideoDatabase


class Application:
    def __init__(self):
        self.app_name = "Pysaurus"
        self.home_dir = AbsolutePath(str(Path.home()))
        self.app_dir = AbsolutePath.join(self.home_dir, f".{self.app_name}").mkdir()
        self.db_path = AbsolutePath.join(self.app_dir, f"databases.db")
        self.lang_dir = AbsolutePath.join(self.app_dir, "languages").mkdir()

        self.db = VideoDatabase(self.db_path.path)
        row = self.db.query_one("SELECT application_id, lang FROM application")
        self.application_id = row[0]
        self.lang = row[1]

        say.set_language(self.lang)
        say.set_folder(self.lang_dir)
