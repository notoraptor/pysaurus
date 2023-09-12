from pysaurus.application.application import Application
from pysaurus.database.database import Database


with open("ignored/db_name.txt") as file:
    DB_NAME = file.read().strip()


def get_database() -> Database:
    app = Application()
    return app.open_database_from_name(DB_NAME)
