"""
How to use black as an API (2024/04/26):
https://stackoverflow.com/a/57653302
"""

import inspect
import os

from black import FileMode, format_str

from pysaurus.core.classes import StringPrinter
from pysaurus.interface.api.gui_api import GuiAPI


def main():
    base_api = GuiAPI()
    with StringPrinter() as printer:
        printer.write("from typing import *")
        printer.write()
        printer.write("from pysaurus.interface.api.gui_api import GuiAPI")
        printer.write()
        printer.write()
        printer.write("class FletApiInterface:")
        printer.write('    __slots__ = ("api",)')
        printer.write()
        printer.write("    def __init__(self, api: GuiAPI):")
        printer.write("        self.api = api")
        printer.write()
        printer.write("    # Proxies")
        printer.write()
        for name, proxy in base_api._proxies.items():
            signature = proxy.get_signature()
            write_method(name, signature, printer)

        printer.write("    # Methods")
        printer.write()
        for name, method in inspect.getmembers(base_api, inspect.ismethod):
            if "a" <= name[0] <= "z":
                signature = inspect.signature(method)
                write_method(name, signature, printer)

        output = str(printer)

    output = format_str(output, mode=FileMode())
    output_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "flet_api_interface.py"
    )
    with open(output_path, "w") as file:
        file.write(output)


def write_method(name: str, signature: inspect.Signature, printer: StringPrinter):
    param_args = None
    param_kwargs = None
    params = []
    for param in signature.parameters.values():
        if param.kind == param.VAR_POSITIONAL:
            param_args = param
        elif param.kind == param.VAR_KEYWORD:
            param_kwargs = param
        elif param.name not in ("self", "cls"):
            params.append(param)
    param_string = ""
    if params:
        param_string = ", " + ", ".join(str(param) for param in params)

    printer.write(f"    def {name}(self{param_string}):")
    printer.write(
        f"        return self.api.__run_feature__({repr(name)}"
        f"{', ' if params else ''}"
        f"{', '.join(param.name for param in params)})"
    )
    printer.write()


if __name__ == "__main__":
    main()
