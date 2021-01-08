from typing import Dict, Callable

from pysaurus.core import exceptions
from pysaurus.core.function_parsing.function_definition import FunctionDefinition


class FunctionParser:
    __slots__ = 'definitions',

    def __init__(self):
        self.definitions = {}  # type: Dict[str, FunctionDefinition]

    def add(self, function, name=None, arguments=None, description=None):
        # type: (callable, str, Dict[str, Callable], str) -> None
        function_definition = FunctionDefinition(function, name, arguments, description)
        assert function_definition.name not in self.definitions
        self.definitions[function_definition.name] = function_definition

    def get_definition(self, function):
        # type: (callable) -> FunctionDefinition
        return self.definitions.get(function.__name__, None)

    def override_definition(self, new_function):
        self.get_definition(new_function).function = new_function

    def remove_definition(self, name_or_function):
        if isinstance(name_or_function, str):
            self.definitions.pop(name_or_function, None)
        elif callable(name_or_function):
            self.definitions.pop(name_or_function.__name__, None)

    def help(self, name=None):
        if name is None:
            for fn_name in sorted(self.definitions):
                print(self.definitions[fn_name])
        elif name in self.definitions:
            print(self.definitions[name])

    def has_name(self, function_name):
        return function_name in self.definitions

    def call(self, function_name, function_args=None):
        if function_name not in self.definitions:
            raise exceptions.UnknownQuery(function_name)
        function_definition = self.definitions[function_name]
        if len(function_args) != len(function_definition.arguments):
            raise exceptions.InvalidQueryArgCount()
        kwargs = {}
        for argument_name, argument_parser in function_definition.arguments.items():
            if argument_name not in function_args:
                raise exceptions.MissingQueryArg(argument_name)
            kwargs[argument_name] = argument_parser(function_args[argument_name])
        return function_definition.function(**kwargs)
