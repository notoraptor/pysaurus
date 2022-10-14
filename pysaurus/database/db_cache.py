import sys


class DbCache:
    __slots__ = "cache", "database", "iteration"

    def __init__(self, database):
        self.cache = {}
        self.database = database
        self.iteration = -1

    def __call__(self, *flags, **forced_flags):
        required = {flag: True for flag in flags}
        required.update(forced_flags)
        required["discarded"] = required.get("discarded", False)
        key = tuple(sorted(required.items()))
        if self.iteration != self.database.iteration:
            self.cache.clear()
            self.iteration = self.database.iteration
        if key not in self.cache:
            self.cache[key] = self.database.query(required)
        else:
            print("Cached", key, file=sys.stderr)
        return self.cache[key]
