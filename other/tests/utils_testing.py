from pysaurus.application.application import Application
from pysaurus.database.database import Database


def get_database() -> Database:
    app = Application()
    return app.open_database_from_name("adult videos")
