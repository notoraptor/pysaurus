import sqlite3


class DbID(int):
    """Wrapper for database ID.

    A database ID should always be evaluated to True if exists, even if its value is 0.

    If a database ID does not exist, database class will return None.

    This wrapper allows to use Python syntax (this_id or that_id) and make sure
    this_id will be returned even if this_id is 0 (we expect this_id to be None if
    related id is invalid or non-existent).
    """

    def __bool__(self):
        return True


class SaurusSQLiteConnection:
    __slots__ = ("connection", "cursor")

    def __init__(self, script_path: str, db_path: str):
        """
        Open (or create) and populate tables (if necessary)
        in database at given path.
        """
        # NB: We must set check_same_thread to False, otherwise
        # we may get following error:
        # sqlite3.ProgrammingError:
        # SQLite objects created in a thread can only be used in that same thread.
        # The object was created in thread id <> and this is thread id <>.
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self.cursor.arraysize = 1000
        with open(script_path) as script_file:
            self.cursor.executescript(script_file.read())
            self.connection.commit()

    def modify(self, query, parameters=(), many=False) -> DbID:
        """
        Execute a modification query (INSERT, UPDATE, etc).
        Return last inserted row ID, or None if no row was inserted.
        """
        if many:
            self.cursor.executemany(query, parameters)
        else:
            self.cursor.execute(query, parameters)
        self.connection.commit()
        last_id = self.cursor.lastrowid
        return last_id if last_id is None else DbID(last_id)

    def modify_many(self, query, parameters=()) -> DbID:
        return self.modify(query, parameters, many=True)

    def query(self, query, parameters=(), debug=False):
        if debug:
            print(f"[query] {query}")
            print(f"[params] {parameters}")
        self.cursor.execute(query, parameters)
        yield from self.cursor

    def query_one(self, query, parameters=()):
        self.cursor.execute(query, parameters)
        return self.cursor.fetchone()

    def query_all(self, query, parameters=()):
        self.cursor.execute(query, parameters)
        return self.cursor.fetchall()

    def insert(self, table: str, **kwargs):
        """Insert a row in a table and return new row ID."""
        columns = list(kwargs)
        values = [kwargs[column] for column in columns]
        return self.modify(
            f"INSERT INTO {table} ({', '.join(columns)}) "
            f"VALUES ({', '.join('?' * len(columns))})",
            values,
        )

    def insert_or_ignore(self, table: str, **kwargs):
        """Insert a row in a table and return new row ID."""
        columns = list(kwargs)
        values = [kwargs[column] for column in columns]
        return self.modify(
            f"INSERT OR IGNORE INTO {table} ({', '.join(columns)}) "
            f"VALUES ({', '.join('?' * len(columns))})",
            values,
        )

    def select_id(self, table, column, where_query, where_parameters=()):
        """
        Select one ID from a table and return it if found, else None.
        If more than 1 ID is found, raise a RuntimeError.
        """
        assert None not in where_parameters
        self.cursor.execute(
            f"SELECT {column} FROM {table} WHERE {where_query}", where_parameters
        )
        results = self.cursor.fetchall()
        if len(results) == 0:
            return None
        elif len(results) == 1:
            return DbID(results[0][0])
        else:
            raise RuntimeError(f"Found {len(results)} entries for {table}.{column}")

    def select_id_from_values(self, table, column, **values):
        where_pieces = []
        where_parameters = []
        for key, value in values.items():
            if value is None:
                where_pieces.append(f"{key} IS NULL")
            else:
                where_pieces.append(f"{key} = ?")
                where_parameters.append(value)
        where_query = " AND ".join(where_pieces)
        self.cursor.execute(
            f"SELECT {column} FROM {table} WHERE {where_query}", where_parameters
        )
        results = self.cursor.fetchall()
        if len(results) == 0:
            return None
        elif len(results) == 1:
            return DbID(results[0][0])
        else:
            raise RuntimeError(f"Found {len(results)} entries for {table}.{column}")

    def count(self, table, column, where_query, where_parameters=()):
        """Select and return count from a table."""
        assert None not in where_parameters
        self.cursor.execute(
            f"SELECT COUNT({column}) FROM {table} WHERE {where_query}", where_parameters
        )
        return self.cursor.fetchone()[0]

    def count_from_values(self, table, column, **values):
        where_pieces = []
        where_parameters = []
        for key, value in values.items():
            if value is None:
                where_pieces.append(f"{key} IS NULL")
            else:
                where_pieces.append(f"{key} = ?")
                where_parameters.append(value)
        where_query = " AND ".join(where_pieces)
        self.cursor.execute(
            f"SELECT COUNT({column}) FROM {table} WHERE {where_query}", where_parameters
        )
        return self.cursor.fetchone()[0]
