import sys
import traceback


class InputInterface:
    def __init__(self):
        self.__definitions = {}

    def add_function(self, function, name, arguments=None):
        # type: (callable, str, dict) -> None
        assert callable(function)
        assert name not in self.__definitions
        if arguments is None:
            arguments = dict()
        for argument_name, argument_parser in arguments.items():
            assert isinstance(argument_name, str)
            assert callable(argument_parser)
        self.__definitions[name] = (function, arguments)

    def _help(self):
        for fn_name in sorted(self.__definitions):
            fn_args = self.__definitions[fn_name][1]
            print('%s(%s)' % (fn_name, ', '.join('%s:%s' % (arg_name, arg_parser.__name__)
                                                 for arg_name, arg_parser in sorted(fn_args.items()))))

    def run(self, title=''):
        if title:
            print()
            print(title)
        while True:
            calling_function = False
            try:
                function_name = input('[function]: ').strip()
                calling_function = True
                if function_name == 'help':
                    self._help()
                elif function_name in ('exit', 'quit'):
                    break
                else:
                    if function_name not in self.__definitions:
                        print(r'\unknown')
                        continue
                    function, arguments = self.__definitions[function_name]
                    kwargs = {}
                    for argument_name, argument_parser in arguments.items():
                        value_string = input('\t[%s]: ' % argument_name).strip()
                        kwargs[argument_name] = argument_parser(value_string)
                    result = function(**kwargs)
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
