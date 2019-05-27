class PropertyValue:
    __slots__ = ('__type', '__value')

    def __init__(self, property_type, raw):
        self.__type = property_type
        self.__value = raw

    @property
    def value(self):
        return set(self.__value) if self.__type.multiple else self.__value

    def type_is(self, property_type):
        return self.__type == property_type
