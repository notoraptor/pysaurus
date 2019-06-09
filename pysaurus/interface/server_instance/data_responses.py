from pysaurus.interface.server.protocol import DataResponse


class _OkData(DataResponse):
    def __init__(self, request_id):
        super(_OkData, self).__init__(request_id, None)


class DatabaseIsLoading(_OkData):
    pass


class DatabaseAlreadyLoaded(_OkData):
    pass
