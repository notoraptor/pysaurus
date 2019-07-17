import math


def generate_moderator_2(v):
    m = (v + math.sqrt(v * v + 4)) / 2

    def function(x):
        return (m * m * x) / (m * x + 1)

    function.__name__ = "f(x) = (%s^2*x)/(%s*x + 1)" % (m, m)
    return function


def generate_moderator(V, b):
    def function(x):
        return (V + b) * x / (x + b)

    function.__name__ = 'f(x) = (%(V)s + %(b)s) * x / (x + %(b)s)' % {'V': V, 'b': b}
    return function


def gen(V, c):
    b = (c * abs(V + c) - abs(c) * (V + c)) / V
    d = - c * (V + b) / (abs(c) + b)

    def function(x):
        return (V + b) * (x + c) / (abs(x + c) + b) + d

    name = 'f(x) = (V + b) * (x + c) / (|x + c| + b) + d'
    name = name.replace('(V + b)', str(V + b)).replace('b', str(b)).replace('c', str(c)).replace('d', str(d))
    function.__name__ = name
    return function


def ultimate_generation(V, h, p):
    m = V * (V * h + V * p - h * h + p * p) / (2 * V * h + V * p - 2 * h * h)
    q = m * h / (h + p)

    assert V > 0
    assert h > 0
    assert p > 0
    assert m > 0

    def function(x):
        return m * (x - h) / (abs(x - h) + p) + q

    name = "f(x)=%(m)s(x-%(h)s)/(|x-%(h)s|+%(p)s)+%(q)s" % dict(m=m, h=h, p=p, q=q)
    function.__name__ = name
    return function


def main():
    V = 10
    for p in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10):
        f = ultimate_generation(V, V/2, p)
        print("with p = %s:" % p, f.__name__)
        print()


if __name__ == '__main__':
    main()
