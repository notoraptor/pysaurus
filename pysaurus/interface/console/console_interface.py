from pysaurus.interface.console.input_interface import InputInterface
from pysaurus.interface.interface import Interface


class ConsoleInterface(InputInterface):
    __slots__ = 'interface',

    def __init__(self):
        super(ConsoleInterface, self).__init__()
        self.interface = Interface()
        self.add_function(self.interface.nb_entries, 'nb_entries')
        self.add_function(self.interface.nb_unreadable, 'nb_unreadable')
        self.add_function(self.interface.nb_not_found, 'nb_not_found')
        self.add_function(self.interface.nb_valid, 'nb_valid')
        self.add_function(self.interface.nb_found, 'nb_found')
        self.add_function(self.interface.nb_thumbnails, 'nb_thumbnails')
        self.add_function(self.interface.valid_size, 'valid_size')
        self.add_function(self.interface.valid_length, 'valid_length')
        self.add_function(self.interface.same_sizes, 'same_sizes')
        self.add_function(self.interface.find, 'find', {'terms': str})
        self.add_function(self.interface.open, 'open', {'video_id': int})
        self.add_function(self.interface.delete, 'delete', {'video_id': int})
        self.add_function(self.interface.info, 'info', {'video_id': int})
        self.add_function(self.interface.clear_not_found, 'clear_not_found')
