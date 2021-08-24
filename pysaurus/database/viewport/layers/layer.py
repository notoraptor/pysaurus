from abc import abstractmethod
from typing import Optional

from pysaurus.database.database import Database
from pysaurus.database.video import Video
from pysaurus.core.functions import deep_equals


class Layer:
    __slots__ = (
        "__sub_layer",
        "parent",
        "__args",
        "__to_update",
        "__filtered",
        "__data",
        "database",
    )
    __props__ = ()

    def __init__(self, database: Database):
        self.__args = {}
        self.__sub_layer = None  # type: Optional[Layer]
        self.__to_update = False
        self.__filtered = None
        self.__data = None
        self.parent = None  # type: Optional[Layer]
        self.database = database
        self.reset_parameters()

    def get_root(self):
        layer = self
        while layer.parent is not None:
            layer = layer.parent
        return layer

    def __log(self, *args, **kwargs):
        print("%s/" % type(self).__name__, *args, **kwargs)

    def set_parent(self, parent):
        self.parent = parent

    def set_sub_layer(self, sub_layer):
        self.__sub_layer = sub_layer
        sub_layer.set_parent(self)
        self.__log("sub-filter", None if self.__sub_layer is None else "set")

    def _set_parameters(self, **kwargs):
        for key in kwargs:
            assert key in self.__props__, (key, self.__props__)
            if key not in self.__args or not deep_equals(kwargs[key], self.__args[key]):
                self.__to_update = True
                self.__args[key] = kwargs[key]
                self.__log("set parameter", key, kwargs[key])

    @property
    def _cache(self):
        return self.__filtered

    def set_data(self, data):
        self.__to_update = True
        self.__data = data
        self.__log(
            "data", None if self.__data is None else "set %s" % type(data).__name__
        )

    def request_update(self):
        self.__to_update = True
        self.__log("update forced")

    def requires_update(self):
        return self.__to_update

    def get_parameter(self, key):
        return self.__args[key]

    def run(self):
        if self.__data is None:
            self.__log("run no data")
            return ()
        if self.__to_update:
            self.__filtered = self.filter(self.__data)
            self.__to_update = False
            self.__log("run")
            if self.__sub_layer:
                self.__sub_layer.set_data(self.__filtered)
                return self.__sub_layer.run()
            else:
                return self.__filtered
        elif self.__sub_layer:
            if self.__sub_layer.requires_update():
                self.__sub_layer.set_data(self.__filtered)
            return self.__sub_layer.run()
        else:
            return self.__filtered

    def delete_video(self, video):
        self.remove_from_cache(self.__filtered, video)
        self.__log("delete", video.filename)
        if self.__sub_layer:
            self.__sub_layer.delete_video(video)

    @abstractmethod
    def reset_parameters(self):
        raise NotImplementedError()

    @abstractmethod
    def filter(self, data):
        raise NotImplementedError()

    @abstractmethod
    def remove_from_cache(self, cache, video: Video):
        raise NotImplementedError()
