import shlex
import sys
import traceback

from pysaurus.interface.console.function_parser import FunctionParser


def command_line_interface(console_parser: FunctionParser):
    print(
        "\n[CONSOLE INTERFACE] "
        '("exit", "e", "quit", "q" or Ctrl+C to exit, "help" or "h" to print help)'
    )

    while True:
        calling_function = False
        try:
            raw_function_name = input("[function]: ").strip()
            calling_function = True
            index_space = raw_function_name.find(" ")
            if index_space < 0:
                function_name = raw_function_name
                function_arg = None
            else:
                function_name = raw_function_name[:index_space]
                function_arg = raw_function_name[index_space:].strip()
            if function_name.lower() in ("exit", "e", "quit", "q"):
                break
            if function_name.lower() in ("help", "h"):
                console_parser.help(name=function_arg)
                continue
            if function_name not in console_parser.definitions:
                print(r"\unknown")
                continue
            function_definition = console_parser.definitions[function_name]
            kwargs = {}
            if function_arg:
                nb_args = len(function_definition.arguments)
                if nb_args == 0:
                    print(r"\error no argument expected")
                    continue
                if nb_args == 1:
                    argument_name, argument_parser = next(
                        iter(function_definition.arguments.items())
                    )
                    kwargs = {argument_name: argument_parser(function_arg)}
                else:
                    arg_list = shlex.split(function_arg)
                    parser = function_definition.to_command_line()
                    args = parser.parse_args(arg_list)
                    kwargs = {
                        argument_name: getattr(args, argument_name)
                        for argument_name in function_definition.arguments
                    }
                    print(kwargs)
            else:
                for (
                    argument_name,
                    argument_parser,
                ) in function_definition.arguments.items():
                    value_string = input("\t[%s]: " % argument_name).strip()
                    kwargs[argument_name] = argument_parser(value_string)
            result = function_definition.function(**kwargs)
            if result is not None:
                print(result)
        except KeyboardInterrupt:
            if calling_function:
                print("\n\\interrupted")
            else:
                print("\n\\exit")
                break
        except Exception as exc:
            traceback.print_tb(exc.__traceback__, file=sys.stdout)
            print(r"\exception", type(exc).__name__, exc)
        print()

    print("End.")
