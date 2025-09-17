import inspect
import os
from typing import Iterable

from saurus.sql import sql_functions
from saurus.sql.skullite import Skullite, SkulliteFunction


class PysaurusConnection(Skullite):
    __slots__ = ()

    def __init__(self, db_path: str):
        super().__init__(
            db_path,
            script_path=os.path.join(os.path.dirname(__file__), "database.sql"),
            functions=self.register_pysaurus_functions(),
        )
        self.register_pysaurus_functions()

    def register_pysaurus_functions(self) -> Iterable[SkulliteFunction]:
        for name, function in inspect.getmembers(
            sql_functions,
            lambda value: callable(value) and value.__name__.startswith("pysaurus_"),
        ):
            signature = inspect.signature(function)
            narg = len(signature.parameters)
            yield SkulliteFunction(
                name=name, function=function, nb_args=narg, deterministic=True
            )
