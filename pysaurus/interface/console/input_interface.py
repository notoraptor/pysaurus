import sys
import traceback


class FunctionDefinition:
    __slots__ = ('function', 'arguments', 'description', 'name')

    def __init__(self, function, name=None, arguments=None, description=None):
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
        return '%s(%s)' % (self.name, ', '.join('%s:%s' % (arg_name, arg_parser.__name__)
                                                for arg_name, arg_parser in sorted(self.arguments.items())))


class InputInterface:
    __slots__ = '__definitions',

    def __init__(self):
        self.__definitions = {}

    def add_function(self, function, name=None, arguments=None, description=None):
        # type: (callable, str, dict, str) -> None
        function_definition = FunctionDefinition(function, name, arguments, description)
        assert function_definition.name not in self.__definitions
        self.__definitions[function_definition.name] = function_definition

    def function_help(self, name=None):
        if name is None:
            for fn_name in sorted(self.__definitions):
                print(self.__definitions[fn_name])
        elif name in self.__definitions:
            function_definition = self.__definitions[name]  # type: FunctionDefinition
            print(function_definition)
            if function_definition.description:
                print(function_definition.description)

    def run(self, title=''):
        if title:
            print()
            print(title)

        while True:
            calling_function = False
            try:
                function_name = input('[function]: ').strip()
                calling_function = True
                if function_name in ('exit', 'quit'):
                    break
                else:
                    index_space = function_name.find(' ')
                    if index_space < 0:
                        if function_name == 'help':
                            self.function_help()
                            continue
                        if function_name not in self.__definitions:
                            print(r'\unknown')
                            continue
                        function_definition = self.__definitions[function_name]  # type: FunctionDefinition
                        kwargs = {}
                        for argument_name, argument_parser in function_definition.arguments.items():
                            value_string = input('\t[%s]: ' % argument_name).strip()
                            kwargs[argument_name] = argument_parser(value_string)
                    else:
                        real_function_name = function_name[:index_space]
                        function_arg = function_name[index_space:].strip()
                        if real_function_name == 'help':
                            self.function_help(function_arg)
                            continue
                        if real_function_name not in self.__definitions:
                            print(r'\unknown')
                            continue
                        function_definition = self.__definitions[real_function_name]  # type: FunctionDefinition
                        if len(function_definition.arguments) != 1:
                            print(r'\error %d arguments expected' % len(function_definition.arguments))
                            continue
                        argument_name, argument_parser = next(iter(function_definition.arguments.items()))
                        kwargs = {argument_name: argument_parser(function_arg)}
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
