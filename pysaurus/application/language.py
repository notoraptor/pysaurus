from pysaurus.application.default_language import DefaultLanguage
from pysaurus.core.functions import class_get_public_attributes


class Language:
    __slots__ = class_get_public_attributes(DefaultLanguage, wrapper=tuple)

    def __init__(self, dct):
        assert isinstance(dct, dict)
        for key in self.__slots__:
            if key in dct:
                value = dct.pop(key)
                assert isinstance(value, (bool, int, float, str))
            else:
                value = getattr(DefaultLanguage, key)
            setattr(self, key, value)
        # assert not dct, dct
