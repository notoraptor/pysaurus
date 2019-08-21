import argparse
import inspect
import textwrap
from typing import Callable, Dict, Optional

from pysaurus.core.utils.classes import StringPrinter


def symbol_to_string(symbol):
    if inspect.isclass(symbol) or inspect.isfunction(symbol) or inspect.ismethod(symbol):
        return symbol.__name__
    return str(symbol)


# Reference (2019/08/20) https://stackoverflow.com/a/14728477


class ArgumentParserError(Exception):
    pass


class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)


class FunctionDefinition:
    __slots__ = ('function', 'arguments', 'description', 'name')

    def __init__(self, function, name=None, arguments=None, description=None):
        # type: (Callable, Optional[str], Optional[Dict], Optional[str]) -> None
        assert callable(function)
        if name is None:
            name = function.__name__
        if arguments is None:
            arguments = dict()
        if description is None:
            description = ''
        for argument_name, argument_parser in arguments.items():
            assert isinstance(argument_name, str)
            assert callable(argument_parser)
        self.function = function
        self.arguments = arguments
        self.description = description
        self.name = name

    def __str__(self):
        printer = StringPrinter()
        if not self.arguments:
            printer.write('%s()' % self.name)
        else:
            printer.write('%s(' % self.name, end='')
            nb_args = len(self.arguments)
            padding = ' ' * (len(self.name) + 1)
            for i, (arg_name, arg_parser) in enumerate(sorted(self.arguments.items())):
                printer.write('%s%s: %s' % (padding if i else '', arg_name, symbol_to_string(arg_parser)),
                              end=('' if i == nb_args - 1 else ',\n'))
            printer.write(')')
        if self.description:
            padding = ' ' * len(self.name)
            for line in textwrap.wrap(self.description, width=(70 - len(padding))):
                printer.write('%s%s' % (padding, line))
        parser = self.to_command_line()
        if parser:
            printer.write(parser.description)
        return str(printer)

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
                for character in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    if character not in short_names:
                        short_names[character] = arg_name
                        added = True
                        break
            if not added:
                raise ValueError(
                    'Unable to get command-line arg short name for function %s and arg %s' % (self.name, arg_name))
        long_names = {}
        for short_name, arg_name in short_names.items():
            place_holder = arg_name.upper()
            helps.append('--%s %s | -%s %s' % (arg_name, place_holder, short_name, place_holder))
            long_names[arg_name] = short_name
        description = None
        if not self.description:
            padding = ' ' * len(self.name)
            description = '%s%s\n%s%s' % (padding, self.name, padding, ('\n%s' % padding).join(helps))
        parser = ThrowingArgumentParser(description=description)
        for arg_name, arg_parser in sorted(self.arguments.items()):
            parser.add_argument('--%s' % arg_name, '-%s' % long_names[arg_name], type=arg_parser, required=True)
        return parser
