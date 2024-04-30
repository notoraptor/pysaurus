import inspect
import logging
from typing import List, Sequence, Tuple, Type

from pysaurus.core.classes import StringPrinter

logger = logging.getLogger(__name__)


class Overridden:
    __slots__ = ("_methods", "_base_signature", "_base_method")

    def __init__(self, polymorph, basename="on"):
        assert not inspect.isclass(polymorph)
        self._methods = {}
        self._base_signature = None
        self._base_method = None
        prefix = f"{basename}_"
        for name, method in inspect.getmembers(polymorph, inspect.ismethod):
            if name == basename or name.startswith(prefix):
                signature = inspect.signature(method)
                annotations = []
                for param in signature.parameters.values():
                    # NB: It seems, if method comes from an instance, then
                    # signature won't contain first `self` parameter.

                    # NB: We don't want *args and **kwargs.
                    if param.kind == param.VAR_POSITIONAL:
                        raise ValueError(
                            f"[overridden/unsupported/*args] "
                            f"{type(polymorph).__name__}.{name}{signature}"
                        )
                    if param.kind == param.VAR_KEYWORD:
                        raise ValueError(
                            f"[overridden/unsupported/**kwargs] "
                            f"{type(polymorph).__name__}.{name}{signature}"
                        )
                    # We require annotation for each param.
                    if param.annotation == param.empty:
                        raise ValueError(
                            f"[overridden/missing/annotation/param:{param}] "
                            f"{type(polymorph).__name__}.{name}{signature}"
                        )
                    annotations.append(param.annotation)

                if name == basename:
                    self._base_method = method
                    self._base_signature = tuple(annotations)
                else:
                    self._methods[tuple(annotations)] = method

    def __call__(self, *args):
        annotation = tuple(type(arg) for arg in args)
        if annotation in self._methods:
            logger.debug(f"[overridden/call] {annotation}")
            return self._methods[annotation](*args)
        if self._base_signature and annotation == self._base_signature:
            logger.debug(f"[overridden/base] {annotation}")
            return self._base_method(*args)
        candidates = [
            (signature, method)
            for signature, method in self._methods.items()
            if len(signature) == len(annotation)
        ]
        if self._base_signature and len(self._base_signature) == len(annotation):
            candidates.append((self._base_signature, self._base_method))
        if not candidates:
            raise RuntimeError(f"[overridden/unsolvable] {annotation}")
        valid_candidates = self._filter_candidates(candidates, annotation)
        if len(valid_candidates) == 1:
            ((signature, method),) = valid_candidates
            logger.debug(f"[overridden/solved] {annotation}\r\n\t{signature}")
            return method(*args)
        else:
            with StringPrinter() as printer:
                printer.write(f"[overridden/many] {annotation}")
                for signature, _ in valid_candidates:
                    printer.write(f"\t{signature}")
                raise RuntimeError(str(printer))

    def _filter_candidates(
        self,
        candidates: List[Tuple[Sequence[Type], callable]],
        annotation: Sequence[Type],
        column: int = 0,
    ):
        assert column < len(annotation)
        acceptable_classes = set(annotation[column].__mro__)
        valid_candidates = [
            candidate
            for candidate in candidates
            if candidate[0][column] in acceptable_classes
        ]
        if not valid_candidates:
            with StringPrinter() as printer:
                printer.write(f"[overriden/unsolvable/{column}] {annotation}")
                for signature in self._methods:
                    printer.write(f"\t{signature}")
                if self._base_signature:
                    printer.write(f"\t{self._base_signature}")
                raise RuntimeError(str(printer))
        next_column = column + 1
        if next_column < len(annotation):
            return self._filter_candidates(valid_candidates, annotation, next_column)
        else:
            return valid_candidates
