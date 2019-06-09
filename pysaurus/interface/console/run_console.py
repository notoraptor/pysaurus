import sys
import traceback

from pysaurus.core.function_parsing.function_definition import FunctionDefinition
from pysaurus.interface.console.console_parser import ConsoleParser


def main():
    console_parser = ConsoleParser()

    print()
    print('[CONSOLE INTERFACE]')

    while True:
        calling_function = False
        try:
            raw_function_name = input('[function]: ').strip()
            calling_function = True
            index_space = raw_function_name.find(' ')
            if index_space < 0:
                function_name = raw_function_name
                function_arg = None
            else:
                function_name = raw_function_name[:index_space]
                function_arg = raw_function_name[index_space:].strip()
            if function_name in ('exit', 'quit'):
                break
            if function_name == 'help':
                console_parser.help(name=function_arg)
                continue
            if function_name not in console_parser.definitions:
                print(r'\unknown')
                continue
            function_definition = console_parser.definitions[function_name]  # type: FunctionDefinition
            kwargs = {}
            if function_arg:
                if len(function_definition.arguments) != 1:
                    print(r'\error %d arguments expected' % len(function_definition.arguments))
                    continue
                argument_name, argument_parser = next(iter(function_definition.arguments.items()))
                kwargs = {argument_name: argument_parser(function_arg)}
            else:
                for argument_name, argument_parser in function_definition.arguments.items():
                    value_string = input('\t[%s]: ' % argument_name).strip()
                    kwargs[argument_name] = argument_parser(value_string)
            result = function_definition.function(**kwargs)
            if result is not None:
                print(result)
        except KeyboardInterrupt:
            if calling_function:
                print('\n\\interrupted')
            else:
                print('\n\\exit')
                break
        except Exception as exc:
            traceback.print_tb(exc.__traceback__, file=sys.stdout)
            print(r'\exception', type(exc).__name__, exc)
        print()

    print('End.')


if __name__ == '__main__':
    main()
