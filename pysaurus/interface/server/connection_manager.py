from typing import Dict, Optional

from pysaurus.interface.server.connection_handler import ConnectionHandler


class ConnectionManager:
    __slots__ = ('__id_to_connection', '__connection_to_id', '__next_id')
    __id_to_connection: Dict[int, ConnectionHandler]
    __connection_to_id: Dict[ConnectionHandler, int]
    __next_id: int

    def __init__(self):
        self.__id_to_connection = {}
        self.__connection_to_id = {}
        self.__next_id = 0

    def _add_connection(self, connection_handler):
        # type: (ConnectionHandler) -> None
        if connection_handler not in self.__connection_to_id:
            self.__connection_to_id[connection_handler] = self.__next_id
            self.__id_to_connection[self.__next_id] = connection_handler
            self.__next_id += 1

    def _remove_connection(self, connection_handler):
        # type: (ConnectionHandler) -> None
        connection_id = self.__connection_to_id.pop(connection_handler, None)
        if connection_id is not None:
            self.__id_to_connection.pop(connection_id)

    def _get_connection_handler(self, connection_id):
        # type: (int) -> Optional[ConnectionHandler]
        return self.__id_to_connection.get(connection_id, None)

    def _connections(self):
        return self.__id_to_connection.items()

    def get_connection_id(self, connection_handler):
        # type: (ConnectionHandler) -> Optional[int]
        return self.__connection_to_id.get(connection_handler, None)

    def count_connections(self):
        # type: () -> int
        return len(self.__connection_to_id)
