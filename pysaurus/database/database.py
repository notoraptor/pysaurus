from pysaurus.database.jsdb.json_database import JsonDatabase
from pysaurus.database.saurus.sql.pysaurus_collection import PysaurusCollection

USE_SQL = True
BaseDatabase = PysaurusCollection if USE_SQL else JsonDatabase
Database = BaseDatabase
