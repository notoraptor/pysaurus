class InputFunctionCaller:
    def __init__(self):
        self.__definitions = {}

    def add(self, function, name, arguments):
        # type: (callable, str, dict) -> None
        assert callable(function)
        assert name not in self.__definitions
        for argument_name, argument_parser in arguments.items():
            assert isinstance(argument_name, str)
            assert callable(argument_parser)
        self.__definitions[name] = (function, arguments)

    def help(self):
        for fn_name, (_, fn_args) in self.__definitions.items():
            print('%s(%s)' % (fn_name, ', '.join('%s:%s' % (arg_name, arg_parser.__name__)
                                                 for arg_name, arg_parser in sorted(fn_args.items()))))

    def call(self):
        calling_function = False
        try:
            function_name = input('[function]: ').strip()
            calling_function = True
            if function_name == 'help':
                self.help()
            else:
                if function_name not in self.__definitions:
                    print(r'\unknown', function_name)
                    return
                function, arguments = self.__definitions[function_name]
                kwargs = {}
                for argument_name, argument_parser in arguments.items():
                    value_string = input('\t[%s]: ' % argument_name).strip()
                    kwargs[argument_name] = argument_parser(value_string)
                result = function(**kwargs)
                if result is not None:
                    print(r'\result: ', result)
        except KeyboardInterrupt:
            print(r'\interrupted')
        except Exception as exc:
            print(r'\exception', type(exc).__name__, exc)
        print()
        return not calling_function


def show(value):
    print('we show', value)


def test(value):
    print('we test', value)


if __name__ == '__main__':
    function_caller = InputFunctionCaller()
    function_caller.add(show, 'show', {'value': str})
    function_caller.add(test, 'test', {'value': int})
    while True:
        stop = function_caller.call()
        if stop:
            break
