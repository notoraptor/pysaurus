import inspect
from typing import Any, Callable, Dict, Type

from other.saurus.gui.html_factory import HTML


class Incrementer:
    __slots__ = ("__curr",)

    def __init__(self, start=0):
        self.__curr = start

    def next(self):
        current = self.__curr
        self.__curr += 1
        return current


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


class Renderer:
    __slots__ = (
        "_method_map",
        "_button_id_counter",
        "_call_id_counter",
        "_script",
        "calls",
        "data",
        "_reverse_calls",
        "header_scripts",
        "body_scripts",
    )

    def __init__(self, data, header_scripts=(), body_scripts=()):
        self._method_map: Dict[Type, Callable[[Any], str]] = {
            str: str,
            bool: str,
            int: str,
            float: str,
            type(None): str,
            tuple: self.render_tuple,
            list: self.render_list,
            dict: self.render_dict,
        }
        self._button_id_counter = Incrementer()
        self._call_id_counter = Incrementer()
        self._script = []
        self._reverse_calls = {}
        self.calls = {}
        self.data = data
        self.header_scripts = header_scripts
        self.body_scripts = body_scripts

    def render_tuple(self, element: tuple):
        """Render a menu of actions"""
        raise NotImplementedError()

    def render_dict(self, element: dict):
        raise NotImplementedError()

    def render_object(self, element: object):
        raise NotImplementedError()

    def render_list(self, element: list):
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
        elif typ in self._method_map:
            # table with one column
            raise NotImplementedError()
        else:
            # Table with rows from an object
            attributes, methods = get_structure(element[0])
            return HTML.table()(
                HTML.thead()(
                    HTML.tr()(
                        *(HTML.th()(attribute) for attribute in attributes),
                        HTML.th()("&nbsp;"),
                    )
                ),
                HTML.tbody()(
                    *(
                        HTML.tr()(
                            *(
                                HTML.td()(self.render(getattr(obj, attribute)))
                                for attribute in attributes
                            ),
                            HTML.td()(
                                *(
                                    HTML.div()(self._render_method(obj, method))
                                    for method in methods
                                )
                            ),
                        )
                        for obj in element
                    )
                ),
            )

    def _render_method(self, instance, method_name):
        key = (id(instance), method_name)
        if key in self._reverse_calls:
            button_id = self._reverse_calls[key]
        else:
            button_id = f"button_{self._button_id_counter.next()}"
            self._script.append(
                f'document.getElementById("{button_id}").onclick = '
                f'() => backend_call("{button_id}");'
            )
            self.calls[button_id] = (instance, method_name)
            self._reverse_calls[key] = button_id
        return f"<button id={button_id}>{method_name}</button>"

    def render_call(self, instance, method_name):
        js_fn_validate_form = []
        tags = []
        method = getattr(instance, method_name)
        for parameter in inspect.signature(method).parameters.values():
            assert parameter.annotation != parameter.empty
            name = parameter.name
            annotation = parameter.annotation
            default = (
                None if parameter.default == parameter.empty else parameter.default
            )
            if annotation in (str, int, float):
                attributes = {"type": "text" if annotation is str else "number"}
                if default is not None:
                    attributes["value"] = default
                tag = HTML.input(name=name, **attributes)

                js_value = f'form["{name}"].value'
                if annotation is int:
                    js_value = f"parseInt({js_value})"
                elif annotation is float:
                    js_value = f"parseFloat({js_value})"
                js_fn_validate_form.append(f"args.{name} = {js_value};")
            elif annotation is bool:
                attributes = {"checked": "checked"} if default else {}
                input_tag = HTML.input(
                    id=name, name=name, type="checkbox", **attributes
                )
                label_tag = HTML.label(html_for=name)(name)
                tag = HTML.div()(input_tag, label_tag)
                js_fn_validate_form.append(f'args.{name} = form["{name}"].checked;')
            else:
                raise NotImplementedError(instance, method_name, name, annotation)
            tags.append(tag)
        if not tags:
            return None
        submit_id = f"call_{self._call_id_counter.next()}"
        tags.append(HTML.button(id=submit_id)(method_name))
        form = HTML.form(name=method_name)(*tags)
        self.calls[submit_id] = (instance, method_name)
        script = [
            f'document.getElementById("{submit_id}").onclick = function() ' + "{",
            [
                "const args = {};",
                f'const form = document.forms["{method_name}"];',
            ],
            js_fn_validate_form,
            [
                f'backend_call("{submit_id}", args);',
            ],
            "}",
        ]
        return str(
            HTML.html(
                HTML.head(
                    *(
                        HTML.script(src=header_script)
                        for header_script in self.header_scripts
                    )
                ),
                HTML.body(
                    form,
                    HTML.script(type="text/javascript")(script),
                    *(
                        HTML.script(src=body_script)
                        for body_script in self.body_scripts
                    ),
                ),
            )
        )

    def render(self, element: Any):
        element_type = type(element)
        if element_type in self._method_map:
            return self._method_map[element_type](element)
        else:
            return self.render_object(element)

    @property
    def html(self):
        ret = HTML.html()(
            HTML.head()(
                *(
                    HTML.script(src=header_script)
                    for header_script in self.header_scripts
                )
            ),
            HTML.body()(
                self.render(self.data),
                HTML.script(type="text/javascript")(
                    "window.onload = function() {",
                    self._script,
                    "};",
                ),
                *(HTML.script(src=body_script) for body_script in self.body_scripts),
            ),
        )
        code = str(ret)
        print("[html]")
        print(code)
        return code
