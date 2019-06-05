""" User object, defined with a username and a hashed password. """
from pysaurus.interface.server.common import is_valid_password


class User:
    """ User class. """
    __slots__ = ['username', 'password_hash']

    def __init__(self, **kwargs):
        self.username = None
        self.password_hash = None

    def is_valid_password(self, password):
        """ Return True if given password matches user hashed password. """
        return is_valid_password(password, self.password_hash)
