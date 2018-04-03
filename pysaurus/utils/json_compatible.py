import ujson as json
from abc import ABC, abstractmethod


class JSONCompatible(ABC):
    @abstractmethod
    def to_json_data(self):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_json_data(cls, json_data, **kwargs):
        raise NotImplementedError()

    def __str__(self):
        return json.dumps(self.to_json_data())

    @classmethod
    def parse(cls, string_repr, **kwargs):
        """ Parse a string representation of this class and return a class instance.
        :param string_repr: expected string representation of this class.
        :param kwargs: optional parameters necessary to build the class instance.
        :return: a class instance.
        :rtype: cls
        """
        return cls.from_json_data(json.loads(string_repr), **kwargs)
