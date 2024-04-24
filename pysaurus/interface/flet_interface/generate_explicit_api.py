import os

from pysaurus.core.classes import StringPrinter
from pysaurus.interface.api.gui_api import GuiAPI


def main():
    base_api = GuiAPI()
    with StringPrinter() as printer:
        printer.write("from typing import *")
        printer.write("from abc import abstractmethod")
        printer.write("from pysaurus.core.notifications import Notification")
        printer.write("from pysaurus.interface.api.gui_api import GuiAPI")
        printer.write()
        printer.write()
        printer.write("class FletApiWrapper(GuiAPI):")
        printer.write("    @abstractmethod")
        printer.write("    def _notify(self, notification: Notification) -> None:")
        printer.write("        raise NotImplementedError()")
        printer.write()
        for name, proxy in base_api._proxies.items():
            signature = proxy.get_signature()
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
                f"        return self._proxies[{repr(name)}]"
                f"({', '.join(param.name for param in params)})"
            )
            printer.write()
        output = str(printer)
    output_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "flet_api_wrapper.py"
    )
    with open(output_path, "w") as file:
        file.write(output)


if __name__ == "__main__":
    main()
