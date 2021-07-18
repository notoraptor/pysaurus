import argparse
import inspect
import textwrap
import typing
from typing import Callable, Dict, Optional
from types import MethodType

from pysaurus.core import exceptions
from pysaurus.core.classes import StringPrinter
from pysaurus.core.functions import is_instance_from_module


class _ArgumentParserError(Exception):
    pass


class _ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise _ArgumentParserError(message)


class FunctionDefinition:
    __slots__ = ("function", "arguments", "description", "name")

    def __init__(self, function, name=None, arguments=None, description=None):
        # type: (Callable, Optional[str], Optional[Dict], Optional[str]) -> None
        assert callable(function)
        if name is None:
            name = function.__name__
        if arguments is None:
            arguments = {}
        if description is None:
            description = ""
        for argument_name, argument_parser in arguments.items():
            assert isinstance(argument_name, str)
            assert callable(argument_parser)
        self.function = function
        self.arguments = arguments
        self.description = description
        self.name = name

    def __str__(self):
        with StringPrinter() as printer:
            if not self.arguments:
                printer.write("%s()" % self.name)
            else:
                printer.write("%s(" % self.name, end="")
                nb_args = len(self.arguments)
                padding = " " * (len(self.name) + 1)
                for i, (arg_name, arg_parser) in enumerate(
                    sorted(self.arguments.items())
                ):
                    printer.write(
                        "%s%s: %s"
                        % (
                            padding if i else "",
                            arg_name,
                            self.__symbol_to_string(arg_parser),
                        ),
                        end=("" if i == nb_args - 1 else ",\n"),
                    )
                printer.write(")")
            if self.description:
                padding = " " * len(self.name)
                for line in textwrap.wrap(self.description, width=(70 - len(padding))):
                    printer.write("%s%s" % (padding, line))
            parser = self.to_command_line()
            if parser:
                printer.write(parser.description)
            return str(printer)

    @staticmethod
    def __symbol_to_string(symbol):
        if (
            inspect.isclass(symbol)
            or inspect.isfunction(symbol)
            or inspect.ismethod(symbol)
        ):
            return symbol.__name__
        return str(symbol)

    def to_command_line(self):
        # type: () -> Optional[argparse.ArgumentParser]
        if len(self.arguments) < 2:
            return None
        helps = []
        short_names = {}
        for arg_name in sorted(self.arguments):
            added = False
            for character in arg_name:
                if character not in short_names:
                    short_names[character] = arg_name
                    added = True
                    break
                elif character.upper() not in short_names:
                    short_names[character.upper()] = arg_name
                    added = True
                    break
                elif character.lower() not in short_names:
                    short_names[character.lower()] = arg_name
                    added = True
                    break
            if not added:
                for character in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
                    if character not in short_names:
                        short_names[character] = arg_name
                        added = True
                        break
            if not added:
                raise ValueError(
                    "Unable to get command-line arg short name for function %s and arg %s"
                    % (self.name, arg_name)
                )
        long_names = {}
        for short_name, arg_name in short_names.items():
            place_holder = arg_name.upper()
            helps.append(
                "--%s %s | -%s %s" % (arg_name, place_holder, short_name, place_holder)
            )
            long_names[arg_name] = short_name
        description = None
        if not self.description:
            padding = " " * len(self.name)
            description = "%s%s\n%s%s" % (
                padding,
                self.name,
                padding,
                ("\n%s" % padding).join(helps),
            )
        parser = _ThrowingArgumentParser(description=description)
        for arg_name, arg_parser in sorted(self.arguments.items()):
            parser.add_argument(
                "--%s" % arg_name,
                "-%s" % long_names[arg_name],
                type=arg_parser,
                required=True,
            )
        return parser


class FunctionParser:
    __slots__ = ("definitions",)

    def __init__(self):
        self.definitions = {}  # type: Dict[str, FunctionDefinition]

    @staticmethod
    def _is_fdef(obj):
        return callable(obj) and hasattr(obj, "__parsers__")

    def import_from(self, obj):
        for name, function in inspect.getmembers(obj, predicate=self._is_fdef):
            signature = inspect.signature(function)
            parsers = function.__parsers__
            if not parsers:
                parsers = []
                for parameter in signature.parameters.values():
                    assert parameter.annotation != inspect.Parameter.empty, parameter.name
                    assert callable(parameter.annotation)
                    assert not is_instance_from_module(typing, parameter.annotation)
                    parsers.append(parameter.annotation)
            assert len(signature.parameters) == len(parsers)
            self.add(function, name, arguments={
                arg_name: parsers[i]
                for i, arg_name in enumerate(signature.parameters)
            })

    def override_from(self, obj):
        nb_overrides = 0
        for func_def in self.definitions.values():
            overrider = getattr(obj, func_def.name, None)
            if not callable(overrider):
                continue
            signature = inspect.signature(overrider)
            assert len(func_def.arguments) == len(signature.parameters)
            assert all(p in func_def.arguments for p in signature.parameters)
            func_def.function = overrider
            nb_overrides += 1
        print("Overridden", nb_overrides)

    def remove_definitions(self, *removals):
        for removal in removals:
            self.remove_definition(removal)

    def add(self, function, name=None, arguments=None, description=None):
        # type: (callable, str, Dict[str, Callable], str) -> None
        function_definition = FunctionDefinition(function, name, arguments, description)
        assert function_definition.name not in self.definitions, function_definition.name
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
            print("\listing", len(self.definitions), "definitions")
            for fn_name in sorted(self.definitions):
                print(self.definitions[fn_name])
            print("\listed", len(self.definitions), "definitions")
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


def fdef(*parsers):
    assert all(callable(p) for p in parsers)
    def decorator(fn):
        fn.__parsers__ = parsers
        return fn
    return decorator


def fsigned(fn):
    fn.__parsers__ = None
    return fn
