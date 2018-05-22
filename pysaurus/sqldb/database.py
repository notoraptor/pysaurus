import os
import sqlite3
from pysaurus.utils.common import PACKAGE_DIR
from pysaurus.utils.exceptions import EntryExistsException

THUMBNAIL_EXTENSION = 'png'

db_file_path = os.path.realpath(os.path.join(PACKAGE_DIR, '.local', 'model.db'))


class Property(object):

    def __init__(self, db, *, name, type_name, is_multiple, default_value=None):
        self.database = db  # type: Database
        self.name = name
        self.type_name = type_name
        self.default_value = default_value
        self.is_multiple = bool(is_multiple)


class Library(object):
    def __init__(self, db, library_id, name):
        self.database = db  # type: Database
        self.library_id = library_id
        self.library_name = name


class Database(object):

    def __init__(self, sql_file_path):
        self.connection = sqlite3.connect(sql_file_path)
        self.cursor = self.connection.cursor()
        self.property_type_name_to_id = {}
        self.property_type_id_to_name = {}
        db_model_path = os.path.realpath(os.path.join(PACKAGE_DIR, 'pysaurus', 'draft', 'model.sql'))
        with open(db_model_path, 'r') as script_file:
            self.cursor.executescript(script_file.read())
            self.connection.commit()
        self.cursor.execute('SELECT property_type_id, property_type_name FROM property_type')
        for result in self.cursor:
            self.property_type_name_to_id[result[1]] = result[0]
            self.property_type_id_to_name[result[0]] = result[1]
        print(self.property_type_name_to_id)

    def __count(self, table_name, field_name, field_value=None):
        query = 'SELECT COUNT(%s) FROM %s' % (field_name, table_name)
        parameters = []
        if field_value is not None:
            query += ' WHERE %s = ?' % field_name
            parameters.append(field_value)
        self.cursor.execute(query, parameters)
        return self.cursor.fetchone()[0]

    def __modify(self, query, parameters=()):
        self.cursor.execute(query, parameters)
        self.connection.commit()

    def has_library(self, name):
        return self.__count('library', 'library_name', name)

    def create_library(self, name):
        if self.has_library(name):
            raise EntryExistsException('library', name)
        self.__modify('INSERT INTO library (library_name, thumbnail_extension) VALUES (?, ?)',
                      [name, THUMBNAIL_EXTENSION])
        return Library(self, self.cursor.lastrowid, name)

    def load_library(self, name):
        self.cursor.execute('SELECT library_id FROM library WHERE library_name = ?', [name])
        results = self.cursor.fetchall()
        if len(results) != 1:
            raise Exception('Invalid library name %s' % [name])
        return Library(self, results[0][0], name)

    def delete_library(self, name):
        self.__modify('DELETE FROM library WHERE library_name = ?', [name])

    def has_unique_property(self, name):
        return self.__count('unique_property', 'unique_property_name', name)

    def has_multiple_property(self, name):
        return self.__count('multiple_property', 'multiple_property_name', name)

    def create_unique_property(self, name, type_name, default_value=None):
        if type_name not in self.property_type_name_to_id:
            raise Exception('Unknown property type %s' % type_name)
        if self.has_unique_property(name):
            raise EntryExistsException('unique_property', name)
        self.__modify('INSERT INTO unique_property (unique_property_name, property_type_id, default_value) '
                      'VALUES (?, ?, ?)', [name, self.property_type_name_to_id[type_name], default_value])

    def create_multiple_property(self, name, type_name):
        if type_name not in self.property_type_name_to_id:
            raise Exception('Unknown property type %s' % type_name)
        if self.has_multiple_property(name):
            raise EntryExistsException('multiple_property', name)
        self.__modify('INSERT INTO multiple_property (multiple_property_name, property_type_id) VALUES (?, ?)',
                      [name, self.property_type_name_to_id[type_name]])

    def update_unique_property(self, name, *, new_name=None, new_type=None, to_multiple=False):
        # TODO
        pass

    def update_multiple_property(self, name, *, new_name=None, new_type=None, to_unique=False):
        # TODO
        pass

    def delete_unique_property(self, name):
        self.__modify('DELETE FROM unique_property WHERE unique_property_name = ?', [name])

    def delete_multiple_property(self, name):
        self.__modify('DELETE FROM multiple_property WHERE multiple_property_name = ?', [name])

    def get_unique_property(self, name):
        self.cursor.execute('SELECT unique_property_id, property_type_id, default_value, '
                            'FROM unique_property WHERE unique_property_name = ?', [name])
        results = self.cursor.fetchall()
        if len(results) != 1:
            raise Exception('Invalid unique property %s' % name)
        default_value = results[0][2]
        property_type_name = self.property_type_id_to_name[results[0][1]]
        return Property(self, name=name, type_name=property_type_name, default_value=default_value, is_multiple=False)

    def get_multiple_property(self, name):
        self.cursor.execute('SELECT multiple_property_id, property_type_id '
                            'FROM multiple_property WHERE multiple_property_name = ?', [name])
        results = self.cursor.fetchall()
        if len(results) != 1:
            raise Exception('Invalid multiple property %s' % name)
        property_type_name = self.property_type_id_to_name[results[0][1]]
        return Property(self, name=name, type_name=property_type_name, is_multiple=True)


database = Database(db_file_path)
library_name = 'test library'
if database.has_library(library_name):
    library = database.load_library(library_name)
    print('Library', library_name, 'already exists with ID', library.library_id)
else:
    library = database.create_library(library_name)
    print('Library', library_name, 'loaded: id', library.library_id)
if database.has_unique_property('location'):
    print('Property location already created.')
else:
    database.create_unique_property('location', 'string', 'america')
