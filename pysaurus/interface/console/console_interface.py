from pysaurus.interface.common.interface import Interface, NbType, FieldType, bool_type
from pysaurus.interface.console.input_interface import InputInterface


class ConsoleInterface(InputInterface):
    __slots__ = 'interface',

    def __init__(self):
        super(ConsoleInterface, self).__init__()
        self.interface = Interface()
        self.add_function(self.interface.valid_size)
        self.add_function(self.interface.valid_length)
        self.add_function(self.interface.same_sizes)
        self.add_function(self.interface.find, arguments={'terms': str})
        self.add_function(self.interface.open, arguments={'video_id': int})
        self.add_function(self.interface.delete, arguments={'video_id': int})
        self.add_function(self.interface.info, arguments={'video_id': int})
        self.add_function(self.interface.clear_not_found)
        self.add_function(self.interface.nb, arguments={'query': NbType})
        self.add_function(self.interface.rename, arguments={'video_id': int, 'new_title': str})
        self.add_function(self.interface.list, arguments={
            'field': FieldType,
            'reverse': bool_type,
            'page_size': int,
            'page_number': int
        })
