""" Common utils symbols used in diplomacy network code. """
import base64
import binascii
import hashlib
import os
from datetime import datetime

import bcrypt

# Datetime since timestamp 0.
from pysaurus.interface.server.server import LOGGER

EPOCH = datetime.utcfromtimestamp(0)


def _sub_hash_password(password):
    """ Hash long password to allow bcrypt to handle password longer than 72 characters. Module private method.
        :param password: password to hash.
        :return: (String) The hashed password.
    """
    # Bcrypt only handles passwords up to 72 characters. We use this hashing method as a work around.
    # Suggested in bcrypt PyPI page (2018/02/08 12:36 EST): https://pypi.python.org/pypi/bcrypt/3.1.0
    return base64.b64encode(hashlib.sha256(password.encode('utf-8')).digest())


def is_valid_password(password, hashed):
    """ Check if password matches hashed.
        :param password: password to check.
        :param hashed: a password hashed with method hash_password().
        :return: (Boolean). Indicates if the password matches the hash.
    """
    return bcrypt.checkpw(_sub_hash_password(password), hashed.encode('utf-8'))


def hash_password(password):
    """ Hash password. Accepts password longer than 72 characters. Public method.
        :param password: The password to hash
        :return: (String). The hashed password.
    """
    return bcrypt.hashpw(_sub_hash_password(password), bcrypt.gensalt(14)).decode('utf-8')


def generate_token(n_bytes=128):
    """ Generate a token with 2 * n_bytes characters (n_bytes bytes encoded in hexadecimal). """
    return binascii.hexlify(os.urandom(n_bytes)).decode('utf-8')


def timestamp_microseconds():
    """ Return current timestamp with microsecond resolution.
        :return: int
    """
    delta = datetime.now() - EPOCH
    return (delta.days * 24 * 60 * 60 + delta.seconds) * 1000000 + delta.microseconds


def ensure_path(folder_path):
    """ Make sure given folder path exists and return given path.
        Raises an exception if path does not exists, cannot be created or is not a folder.
    """
    if not os.path.exists(folder_path):
        LOGGER.info('Creating folder %s', folder_path)
        os.makedirs(folder_path, exist_ok=True)
    if not os.path.isdir(folder_path):
        raise OSError('Path is not a directory: %s' % folder_path)
    return folder_path
