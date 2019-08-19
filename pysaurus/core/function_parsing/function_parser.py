from typing import Dict

from pysaurus.core.function_parsing import function_parsing_errors
from pysaurus.core.function_parsing.function_definition import FunctionDefinition


class FunctionParser:
    __slots__ = 'definitions',

    def __init__(self):
        self.definitions = {}  # type: Dict[str, FunctionDefinition]

    def add(self, function, name=None, arguments=None, description=None):
        # type: (callable, str, dict, str) -> None
        function_definition = FunctionDefinition(function, name, arguments, description)
        assert function_definition.name not in self.definitions
        self.definitions[function_definition.name] = function_definition

    def has_name(self, function_name):
        return function_name in self.definitions

    def get_definition(self, function):
        # type: (callable) -> FunctionDefinition
        return self.definitions.get(function.__name__, None)

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
            function_definition = self.definitions[name]
            print(function_definition)
            if function_definition.description:
                print(function_definition.description)

    def call(self, function_name, function_args=None):
        if function_name not in self.definitions:
            raise function_parsing_errors.UnknownQuery(function_name)
        function_definition = self.definitions[function_name]
        if len(function_args) != len(function_definition.arguments):
            raise function_parsing_errors.InvalidQueryArgCount()
        kwargs = {}
        for argument_name, argument_parser in function_definition.arguments.items():
            if argument_name not in function_args:
                raise function_parsing_errors.MissingQueryArg(argument_name)
            kwargs[argument_name] = argument_parser(str(function_args[argument_name]).strip())
        return function_definition.function(**kwargs)
