
INTEGER = 'integer'
UNSIGNED = 'unsigned'
FLOAT = 'float'
STRING = 'string'

ONE = 'one'
MANY = 'many'

TAG_TYPES = {INTEGER, UNSIGNED, FLOAT, STRING}
TAG_DIMENSIONS = {ONE, MANY}


class Tag(object):
    __slots__ = ['tag_name', 'tag_dimension', 'tag_type', 'tag_values', 'tag_default']
    def __init__(self, tag_name, tag_type, tag_dimension=ONE, tag_values=None, tag_default=None):
        if not tag_name or not isinstance(tag_name, str):
            raise Exception('Expected a valid tag name, got %s' % tag_name)
        if tag_type not in TAG_TYPES:
            raise Exception('Expected a valid tag type (%s), got %s' % (', '.join(TAG_TYPES), tag_type))
        if tag_dimension not in TAG_DIMENSIONS:
            raise Exception('Expected a valid tag dimension: (%s), got %s' % (', '.join(TAG_DIMENSIONS), tag_dimension))
        if not tag_values:
            tag_values = set()
        else:
            try:
                tag_values = set(tag_values)
            except Exception:
                raise Exception('Invalid sequence of tag values: %s' % tag_values)
        if not tag_default:
            tag_default = None
        elif tag_values and tag_default not in tag_values:
            raise Exception('Invalid tag default value, expected (%s), got %s' % (', '.join(tag_values), tag_default))
        self.tag_name = tag_name
        self.tag_type = tag_type
        self.tag_dimension = tag_dimension
        self.tag_values = tag_values
        self.tag_default = tag_default

    def to_dict(self):
        return {name: getattr(self, name) for name in self.__slots__}

    def from_dict(self, dct: dict):
        return Tag(**dct)
