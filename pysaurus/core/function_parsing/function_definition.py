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
        return '%s(%s)' % (self.name, ', '.join(
            '%s:%s' % (arg_name, arg_parser.__name__) for arg_name, arg_parser in sorted(self.arguments.items())))
