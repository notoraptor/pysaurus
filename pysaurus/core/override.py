import inspect


class Override:
    __slots__ = "mapping", "with_any", "nb_methods", "name"

    def __init__(self, name=None):
        self.mapping = {}
        self.with_any = {}
        self.nb_methods = 0
        self.name = name or type(self).__name__

    def __str__(self):
        signatures = list(self.mapping) + list(self.with_any)
        if signatures:
            return (
                f"{self.name}{{\n" + ("\n".join(str(sig) for sig in signatures)) + "\n}"
            )
        else:
            return f"{self.name}{{no signature}}"

    __repr__ = __str__

    def _identify(self, fn):
        annotations = []
        for i, parameter in enumerate(inspect.signature(fn).parameters.values()):
            if parameter.annotation is parameter.empty:
                assert i == 0
                assert parameter.name == "self"
                cls_name, fn_name = fn.__qualname__.split(".")
                assert fn_name == fn.__name__
                annotations.append(cls_name)
                self.nb_methods += 1
            else:
                assert isinstance(parameter.annotation, type)
                annotations.append(parameter.annotation)
        return tuple(annotations)

    def override(self, fn):
        identifier = self._identify(fn)
        if object in identifier:
            assert identifier not in self.with_any
            self.with_any[identifier] = fn
        else:
            assert identifier not in self.mapping
            self.mapping[identifier] = fn
        assert not self.nb_methods or (
            self.nb_methods == len(self.mapping) + len(self.with_any)
        )
        ovr = self

        def wrapper(*args, **kwargs):
            return ovr(*args, **kwargs)

        wrapper.override = ovr.override
        return wrapper

    def __call__(self, *args, **kwargs):
        initial_identifier = [type(arg) for arg in args] + [
            type(value) for value in kwargs.values()
        ]
        if self.nb_methods:
            cls = initial_identifier[0]
            cls_seq = cls.__mro__
            assert cls_seq[0] is cls
            assert cls_seq[-1] is object
            remaining_identifier = tuple(initial_identifier[1:])
            identifiers = [
                (mro_cls.__name__,) + remaining_identifier for mro_cls in cls_seq[:-1]
            ]
        else:
            identifiers = [tuple(initial_identifier)]
        # Check in mapping first.
        for identifier in identifiers:
            if identifier in self.mapping:
                return self.mapping[identifier](*args, **kwargs)
        # Then check in with_any.
        for identifier in identifiers:
            for generic_sig, fn in self.with_any.items():
                if len(identifier) == len(generic_sig) and all(
                    a is object or a == b for a, b in zip(generic_sig, identifier)
                ):
                    return fn(*args, **kwargs)
        raise KeyError(initial_identifier, self)
