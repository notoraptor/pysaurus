from pysaurus.application.language.default_language import DefaultLanguage
from pysaurus.core.functions import class_get_public_attributes


class Language(DefaultLanguage):
    __slots__ = class_get_public_attributes(DefaultLanguage, wrapper=tuple) + (
        "__language__",
        "__updated__",
    )

    def __init__(self, dct, name):
        assert isinstance(dct, dict)
        updated = 0
        for key in self.__slots__[:-2]:
            if key in dct:
                value = dct.pop(key)
                assert isinstance(value, (bool, int, float, str))
            else:
                value = getattr(DefaultLanguage, key)
                updated += 1
            setattr(self, key, value)
        self.__language__ = name
        self.__updated__ = updated + len(dct)
