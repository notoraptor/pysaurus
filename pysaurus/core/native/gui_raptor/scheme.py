class Field:
    bold = "bold"
    color = "color"
    content = "content"
    coordinates = "coordinates"
    count = "count"
    font = "font"
    height = "height"
    italic = "italic"
    left = "left"
    length = "length"
    outline = "outline"
    outline_color = "outlineColor"
    patterns = "patterns"
    size = "size"
    src = "src"
    strike = "strike"
    top = "top"
    underline = "underline"
    width = "width"
    x = "x"
    y = "y"


class Scheme:
    ATTRIBUTES = ()


class Text(Scheme):
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
    ATTRIBUTES = [
        Field.bold,
        Field.color,
        Field.content,
        Field.font,
        Field.italic,
        Field.outline,
        Field.outline_color,
        Field.size,
        Field.strike,
        Field.underline,
        Field.x,
        Field.y,
    ]


class Frame(Scheme):
    x = Field.x
    y = Field.y
    width = Field.width
    height = Field.height
    count = Field.count
    patterns = Field.patterns
    ATTRIBUTES = [
        Field.count,
        Field.height,
        Field.patterns,
        Field.width,
        Field.x,
        Field.y,
    ]


class Image(Scheme):
    x = Field.x
    y = Field.y
    width = Field.width
    height = Field.height
    src = Field.src
    ATTRIBUTES = [Field.height, Field.src, Field.width, Field.x, Field.y]


class Rectangle(Scheme):
    x = Field.x
    y = Field.y
    width = Field.width
    height = Field.height
    outline = Field.outline
    color = Field.color
    outline_color = Field.outline_color
    ATTRIBUTES = [
        Field.color,
        Field.height,
        Field.outline,
        Field.outline_color,
        Field.width,
        Field.x,
        Field.y,
    ]
