class A:
    parent = None

    def __init__(self):
        print("Parent:", self.parent)


class B:
    def __init__(self, value):
        cls = self.sub_a()
        self.v = value
        self.a = cls()

    def __str__(self):
        return f"{type(self).__name__}(v={self.v})"

    def sub_a(self):
        class AA(A):
            parent = self

        return AA


B(0)
B(1)
B(-1)
