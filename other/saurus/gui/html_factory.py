def indent_string_tree(tree: list, indent=""):
    return "\n".join(
        (
            indent_string_tree(entry, indent + "\t")
            if isinstance(entry, list)
            else f"{indent}{entry}"
        )
        for entry in tree
    )


class Tag:
    __slots__ = ("name", "void", "attributes", "children", "__repr_compact")

    def __init__(
        self, tag_name: str, is_void: bool, class_name=None, html_for=None, **attributes
    ):
        if class_name is not None:
            attributes["class"] = class_name
        if html_for is not None:
            attributes["for"] = html_for
        self.name = tag_name
        self.void = is_void
        self.attributes = attributes
        self.children = []
        self.__repr_compact = False

    def __call__(self, *children):
        self.children.extend(children)
        return self

    def __str__(self):
        return (
            self.__str_compact()
            if self.__repr_compact
            else indent_string_tree(self.tree())
        )

    def compact(self):
        self.__repr_compact = True
        return self

    def indented(self):
        self.__repr_compact = False
        return self

    def __str_compact(self):
        code = f"<{self.name}"
        if self.attributes:
            for key, value in self.attributes.items():
                code += f' {key}="{value}"'
        if self.void:
            assert not self.children
            code += "/"
        else:
            code += ">"
            for child in self.children:
                code += str(child)
            code += f"</{self.name}"
        code += ">"
        return code

    def tree(self):
        code = f"<{self.name}"
        if self.attributes:
            for key, value in self.attributes.items():
                code += f' {key}="{value}"'
        if self.void:
            assert not self.children
            return [code + "/>"]
        else:
            output = [code + ">"]
            for child in self.children:
                if isinstance(child, Tag):
                    output.append(child.tree())
                elif isinstance(child, list):
                    output.append(child)
                else:
                    output.append(str(child))
            output.append(f"</{self.name}>")
            if len(output) == 2 or (len(output) == 3 and isinstance(output[1], str)):
                return ["".join(output)]
            else:
                return output


class TagFactory:
    __slots__ = "tag_name", "is_void"

    def __init__(self, tag_name: str, is_void: bool):
        self.tag_name = tag_name
        self.is_void = is_void

    def __call__(self, *children, class_name=None, html_for=None, **attributes):
        return Tag(
            self.tag_name,
            self.is_void,
            class_name=class_name,
            html_for=html_for,
            **attributes,
        )(*children)


class HtmlFactory:
    """
    Factory class to generate HTML Tag objects.
    Module provides a singleton `HTML` to use this class.

    Syntaxe:
        my_tag = HTML.<tagname>(**tag_attributes)(*tag_children)
        # or
        my_tag = HTML.<tagname>(*tag_children, **tag_attributes)
    If no attributed needed:
        my_tag = HTML.<tagname>(*tag_children)
    If no children needed:
        my_tag = HTML.<tagname>()
        my_tag = HTML.<tagname>(**tag_attributes)

    Tags listed in __void__ class member are forced to be rendered as void elements.
        my_tag = HTML.input()  # <input/>

    Tag name that ends with an underscore is rendered as a void element, with leading
    underscore ignored.
        my_tag = HTML.rectangle_()  # <rectangle/>

    Syntax provides some convenient tag attributes to handle special tags:
    - `class_name`, rendered as `class` attribute
    - `html_for`, rendered as `for` attribute (e.g. for `label` tag)

        my_tag = HTML.label(class_name="my-label", html_for="my-id")
        # <label class="my-label" for="my-id"></label>

    A list in children is automatically printed with one indentation and each list entry
    one a new line (with "\n" to introduce new line). This may be helpful for e.g. to
    write a script.
        HTML.script(type="text/javascript")(
            "function(x) {",
            [
                "const y = 2 * x + 1;",
                "return y;",
            ],
            "}",
        )

    Example:
            HTML.div(class_name="my-div")(
                HTML.img(),
                HTML.input(type="text"),
                HTML.br(),
                HTML.span("hello"),
                "another text here",
                HTML.script(
                    "const x = 2;",
                    "console.log(x),
                    "function() {",
                    [
                        "// function code here",
                        "return 0;",
                    ],
                    "}",
                ),
            )
    """

    __slots__ = ()
    __void__ = {
        "area",
        "base",
        "br",
        "col",
        "command",
        "embed",
        "hr",
        "img",
        "input",
        "keygen",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __getattr__(self, tag: str) -> TagFactory:
        tag = tag.lower()
        if tag in self.__void__:
            is_void = True
        elif tag.endswith("_"):
            is_void = True
            tag = tag[:-1]
        else:
            is_void = False

        return TagFactory(tag, is_void)


HTML = HtmlFactory()


if __name__ == "__main__":
    print(HTML.span())
    print(HTML.br())
    print(HTML.atag_())
    print(HTML.div(class_name="Hello")(HTML.span(), HTML.rectangle_()))
    print(HTML.div("hello", "world"))
