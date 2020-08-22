def decorator(function, value):
    def wrapper(*args, **kwargs):
        return value * function(*args, **kwargs)

    return wrapper


class A:
    def __init__(self):
        self.value = 10

    def f(self):
        return self.value * 10


class B(A):
    f = decorator(A.f, 2)


if __name__ == '__main__':
    print(A().f())
    print(B().f())
