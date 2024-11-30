import inspect
from dataclasses import dataclass
from typing import Sequence

from wip.adnoide.adnoide import Protein
from wip.adnoide.mutation import Individual


@dataclass(slots=True)
class Survival:
    individual: Individual
    instability: float

    @property
    def key(self):
        return self.instability, len(self.individual.gene)

    def __lt__(self, other: "Survival"):
        return self.key < other.key


class NaturalSelection:
    __slots__ = ("_inputs", "_outputs", "_nb_args")

    def __init__(self, inputs: Sequence, outputs: Sequence[float]):
        assert len(inputs) == len(outputs)
        inputs = [inp if isinstance(inp, (list, tuple)) else (inp,) for inp in inputs]
        (self._nb_args,) = {len(inp) for inp in inputs}
        self._inputs = inputs
        self._outputs = outputs

    @property
    def feed_size(self) -> int:
        return self._nb_args

    @classmethod
    def from_function(cls, function: callable, inputs: Sequence):
        sig = inspect.signature(function)
        for parameter in sig.parameters.values():
            assert parameter.kind not in (
                parameter.VAR_POSITIONAL,
                parameter.KEYWORD_ONLY,
                parameter.VAR_KEYWORD,
            )
        nb_args = len(sig.parameters)
        formatted_inputs = []
        outputs = []
        for inp in inputs:
            if not isinstance(inp, (list, tuple)):
                assert nb_args == 1
                inp = (inp,)
            formatted_inputs.append(inp)
            outputs.append(function(*inp))
        return cls(formatted_inputs, outputs)

    def survive(self, individual: Individual) -> Survival:
        protein = individual.protein
        distance = sum(
            abs(expected_y - protein(*args))
            for args, expected_y in zip(self._inputs, self._outputs)
        ) / len(self._inputs)
        return Survival(individual=individual, instability=distance)

    def debug(self, protein: Protein):
        for args, expected in zip(self._inputs, self._outputs):
            given = protein(*args)
            print(f"f({', '.join(str(x) for x in args)}) = {expected}")
            if expected != given:
                print("\tgot:", given)
