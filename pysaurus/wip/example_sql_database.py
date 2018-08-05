import sqlite3


class Database(object):

    def __init__(self, sql_file_path):
        self.connection = sqlite3.connect(sql_file_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self.property_type_name_to_id = {}
        self.property_type_id_to_name = {}
        with open('model.sql', 'r') as script_file:
            self.cursor.executescript(script_file.read())
            self.connection.commit()
        self.cursor.execute('SELECT property_type_id, property_type_name FROM property_type')
        for result in self.cursor:
            self.property_type_name_to_id[result[1]] = result[0]
            self.property_type_id_to_name[result[0]] = result[1]
        print(self.property_type_name_to_id)

    def modify(self, query, parameters=()):
        self.cursor.execute(query, parameters)
        self.connection.commit()

    def example_load_library(self, name):
        self.cursor.execute('SELECT library_id FROM library WHERE library_name = ?', [name])
        results = self.cursor.fetchall()
        if len(results) != 1:
            raise Exception('Invalid library name %s' % [name])

    def example_delete_library(self, name):
        self.modify('DELETE FROM library WHERE library_name = ?', [name])

    def example_create_unique_property(self, name, type_name, default_value=None):
        self.modify('INSERT INTO unique_property (unique_property_name, property_type_id, default_value) '
                    'VALUES (?, ?, ?)', [name, self.property_type_name_to_id[type_name], default_value])
