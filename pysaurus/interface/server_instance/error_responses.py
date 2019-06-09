from pysaurus.interface.server.protocol import Request, ErrorResponse


class ErrroUnknownRequest(ErrorResponse):
    def __init__(self, request):
        # type: (Request) -> None
        super(ErrroUnknownRequest, self).__init__(request.request_id, request.name)
