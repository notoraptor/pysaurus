from pysaurus.database.jsdb.json_database import JsonDatabase
from saurus.sql.pysaurus_collection import PysaurusCollection

USE_SQL = False
BaseDatabase = PysaurusCollection if USE_SQL else JsonDatabase
Database = BaseDatabase
