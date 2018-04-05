import concurrent.futures
import math

from pysaurus.utils.profiling import Profiler

PRIMES = [
    112272535095293,
    112582705942171,
    112272535095293,
    115280095190773,
    115797848077099,
    1099726899285419,
    434393658478374387432,
    32224343494273273232,
    3223273271101982873,
    3223273971101982873,
    233223273971101982873,
    23559943223273971101982873,
    3201938273232453434333,
    3201938273232453434333363,
    320193827323245340293874363,
]


def is_prime(n):
    if n % 2 == 0:
        return False

    sqrt_n = int(math.floor(math.sqrt(n)))
    for i in range(3, sqrt_n + 1, 2):
        if n % i == 0:
            return False
    return True


def all_prime():
    for prime in PRIMES:
        is_prime(prime)


def main():
    with Profiler(exit_message='With multiprocessing'):
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [executor.submit(all_prime) for _ in range(4)]
            results = [f.result() for f in futures]
    with Profiler(exit_message='Without multiprocessing:'):
        computed = [all_prime() for _ in range(4)]


if __name__ == '__main__':
    main()
