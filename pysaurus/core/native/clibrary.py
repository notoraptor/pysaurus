import sys
from ctypes import c_char_p, cdll


def c_library(name):
    if sys.platform == 'linux':
        dll = cdll.LoadLibrary('%s.so' % name)
    else:
        dll = getattr(cdll, name)
    return dll


def c_prototype(dll, name, res_type, arg_types):
    symbol = getattr(dll, name)
    if res_type:
        symbol.restype = res_type
    if arg_types:
        symbol.argtypes = arg_types
    return symbol


class CFunction:
    __slots__ = ['__c_func', '__c_args']

    def __init__(self, library, name, restype, argtypes):
        self.__c_args = None if argtypes is None else list(argtypes)
        self.__c_func = c_prototype(library, name, restype, self.__c_args)

    def __call__(self, *args):
        values = []
        if self.__c_args:
            for i, c_arg in enumerate(self.__c_args):
                if c_arg is c_char_p and isinstance(args[i], str):
                    values.append(c_char_p(args[i].encode()))
                else:
                    values.append(args[i])
        return self.__c_func(*values)


class CLibrary:
    __slots__ = ['library']

    def __init__(self, name):
        self.library = c_library(name)

    def prototype(self, name, restype, argtypes):
        return CFunction(self.library, name, restype, argtypes)
