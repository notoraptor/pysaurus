class PropertyError(Exception):
    pass


class PropertyAllowedError(PropertyError):
    def __init__(self, expected_enumeration, given_value):
        super(PropertyAllowedError, self).__init__('expected to be in %s, got %s' % (expected_enumeration, given_value))


class PropertyValueTypeError(PropertyError):
    def __init__(self, expected_type, given_value):
        super(PropertyValueTypeError, self).__init__('expected %s, got %s' % (expected_type, type(given_value)))


class PropertyEnumTypeError(PropertyValueTypeError):
    pass


class PropertyDefaultTypeError(PropertyValueTypeError):
    pass


class PropertyIterableError(PropertyError):
    def __init__(self, given):
        super(PropertyIterableError, self).__init__('expected a basic iterable, got type %s' % type(given))


class PropertyIterableEnumError(PropertyIterableError):
    pass


class PropertyIterableDefaultError(PropertyIterableError):
    pass


class PropertyNameError(PropertyError):
    def __init__(self, name):
        super(PropertyNameError, self).__init__('expected a string with letters, digits or underscore, got %s' % name)


class PropertyTypeError(PropertyError):
    def __init__(self, given_type):
        super(PropertyTypeError, self).__init__('expected a basic type, got %s' % given_type)
