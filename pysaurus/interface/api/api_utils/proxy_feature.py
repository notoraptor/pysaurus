import inspect
from typing import Any, Callable

from pysaurus.core import tk_utils


class ProxyFeature:
    __slots__ = ("proxy",)

    def __init__(self, getter: Callable[[], Any], method: Callable, returns=False):
        self.proxy = (getter, method, returns)

    def __call__(self, *args):
        getter, method, returns = self.proxy
        ret = getattr(getter(), method.__name__)(*args)
        return ret if returns else None

    def __str__(self):
        _, method, returns = self.proxy
        return self.info_signature(method, returns)

    def get_signature(self) -> inspect.Signature:
        _, method, returns = self.proxy
        return inspect.signature(method)

    @classmethod
    def info_signature(cls, method, returns) -> str:
        try:
            ms = inspect.signature(method)
            ret_ann = ms.return_annotation
            ret_accounted = ""
            if ret_ann is ms.empty:
                ret_ann = "undefined"
                if returns:
                    ret_accounted = " (returned)"
            elif not returns and ret_ann is not None:
                ret_accounted = " (ignored)"
            return f"{method.__qualname__} -> {ret_ann}" + ret_accounted
        except Exception as exc:
            raise Exception(method) from exc


class FromDb(ProxyFeature):
    __slots__ = ()

    def __init__(self, api, method, returns=False):
        super().__init__(getter=lambda: api.database, method=method, returns=returns)


class FromView(ProxyFeature):
    __slots__ = ()

    def __init__(self, api, method, returns=False):
        super().__init__(
            getter=lambda: api.database.provider, method=method, returns=returns
        )


class FromApp(ProxyFeature):
    __slots__ = ()

    def __init__(self, api, method, returns=False):
        super().__init__(getter=lambda: api.application, method=method, returns=returns)


class FromTk(ProxyFeature):
    __slots__ = ()

    def __init__(self, method, returns=False):
        super().__init__(getter=lambda: tk_utils, method=method, returns=returns)


class FromPyperclip(ProxyFeature):
    __slots__ = ()

    def __init__(self, method, returns=False):
        import pyperclip

        super().__init__(getter=lambda: pyperclip, method=method, returns=returns)
