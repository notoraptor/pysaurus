def get_structure(obj):
    """
    Retrieve attributes and methods from given object.
    Object must be an instance, not a type or class.

    returns:
        A couple of tuples: (attributes names), (methods names)
    """
    assert not isinstance(obj, type)
    if hasattr(obj, "__slots__"):
        attributes = tuple(obj.__slots__)
    else:
        attributes = tuple(obj.__dict__)
    attr_set = set(attributes)
    methods = []
    for key, value in type(obj).__dict__.items():
        if callable(value) and not key.startswith("_") and key not in attr_set:
            methods.append(key)
    return attributes, tuple(methods)


def indent_string_tree(tree: list, indent=""):
    output = []
    for entry in tree:
        if isinstance(entry, list):
            output.append(indent_string_tree(entry, indent + "\t"))
        else:
            output.append(f"{indent}{entry}")
    return "\n".join(output)


def render_str(element: str):
    return element


def render_bool(element: bool):
    return str(element)


def render_int(element: int):
    return str(element)


def render_float(element: float):
    return str(element)


def render_none(element: type(None)):
    return str(element)


def render_list(element: list):
    """Render a table."""
    if not element:
        return ""
    types = {type(el) for el in element}
    assert len(types) == 1
    typ = next(iter(types))
    if typ is list:
        # Table with rows
        raise NotImplementedError()
    elif typ is dict:
        # Table with rows from a dict
        raise NotImplementedError()
    elif typ in __default_render__:
        # table with one column
        raise NotImplementedError()
    else:
        # Table with rows from an object
        attributes, _ = get_structure(element[0])
        return indent_string_tree(
            [
                "<table>",
                [
                    "<thead>",
                    [
                        "<tr>",
                        [f"<th>{attribute}</th>" for attribute in attributes],
                        "</tr>",
                    ],
                    "</thead>",
                ],
                [
                    "<tbody>",
                    [
                        [
                            "<tr>",
                            [
                                f"<td>{render(getattr(obj, attribute))}</td>"
                                for attribute in attributes
                            ],
                            "</tr>",
                        ]
                        for obj in element
                    ],
                    "</tbody>",
                ],
                "</table>",
            ]
        )


def render_tuple(element: tuple):
    """Render a menu of actions"""
    raise NotImplementedError()


def render_dict(element: dict):
    raise NotImplementedError()


def render_object(element: object):
    raise NotImplementedError()


__default_render__ = {
    str: render_str,
    bool: render_bool,
    int: render_int,
    float: render_float,
    type(None): render_none,
    tuple: render_tuple,
    list: render_list,
    dict: render_dict,
}


def render(element):
    element_type = type(element)
    if element_type in __default_render__:
        return __default_render__[element_type](element)
    else:
        return render_object(element)
