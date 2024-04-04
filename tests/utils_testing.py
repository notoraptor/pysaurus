import json
import os

from pysaurus.application.application import Application
from pysaurus.database.abstract_database import AbstractDatabase

with open(os.path.join(os.path.dirname(__file__), "ignored/db_name.json")) as file:
    DB_INFO = json.load(file)
    DB_NAME = DB_INFO["name"]


def get_database() -> AbstractDatabase:
    app = Application()
    return app.open_database_from_name(DB_NAME)
