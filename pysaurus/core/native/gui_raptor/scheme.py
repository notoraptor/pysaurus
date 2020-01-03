import inspect


def public_static_attributes_of(cls):
    for name, value in inspect.getmembers(cls):
        if not name.startswith('__') and isinstance(value, str):
            yield name


def repr_fields(cls):
    fields = sorted(public_static_attributes_of(cls))
    return '%s.ATTRIBUTES = [%s]' % (cls.__name__, ', '.join('Field.%s' % field for field in fields))


class Field:
    bold = 'bold'
    color = 'color'
    content = 'content'
    coordinates = 'coordinates'
    count = 'count'
    font = 'font'
    height = 'height'
    italic = 'italic'
    left = 'left'
    length = 'length'
    outline = 'outline'
    outline_color = 'outlineColor'
    patterns = 'patterns'
    size = 'size'
    src = 'src'
    strike = 'strike'
    top = 'top'
    underline = 'underline'
    width = 'width'
    x = 'x'
    y = 'y'


class Text:
    x = Field.x
    y = Field.y
    font = Field.font
    content = Field.content
    size = Field.size
    outline = Field.outline
    color = Field.color
    outline_color = Field.outline_color
    bold = Field.bold
    italic = Field.italic
    underline = Field.underline
    strike = Field.strike
    ATTRIBUTES = [Field.bold, Field.color, Field.content, Field.font, Field.italic, Field.outline, Field.outline_color,
                  Field.size, Field.strike, Field.underline, Field.x, Field.y]


class Frame:
    x = Field.x
    y = Field.y
    width = Field.width
    height = Field.height
    count = Field.count
    patterns = Field.patterns
    ATTRIBUTES = [Field.count, Field.height, Field.patterns, Field.width, Field.x, Field.y]


class Image:
    x = Field.x
    y = Field.y
    width = Field.width
    height = Field.height
    src = Field.src
    ATTRIBUTES = [Field.height, Field.src, Field.width, Field.x, Field.y]


class Rectangle:
    x = Field.x
    y = Field.y
    width = Field.width
    height = Field.height
    outline = Field.outline
    color = Field.color
    outline_color = Field.outline_color
    ATTRIBUTES = [Field.color, Field.height, Field.outline, Field.outline_color, Field.width, Field.x, Field.y]


if __name__ == '__main__':
    print(repr_fields(Text))
    print(repr_fields(Frame))
    print(repr_fields(Image))
    print(repr_fields(Rectangle))
