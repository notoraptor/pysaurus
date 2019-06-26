import os

from pysaurus.core.utils.functions import dispatch_combinations, count_couples


def main():
    n = 14000
    cpu_count = os.cpu_count()
    nb_couples = count_couples(n)
    batch_size = int(nb_couples / cpu_count)
    intervals = dispatch_combinations(n, cpu_count)
    print('n:', n)
    print('CPU count:', cpu_count)
    print('number of couples:', nb_couples)
    print('Batch size:', batch_size)
    print('Number of intervals:', len(intervals))
    if len(intervals) < 100:
        for interval in intervals:
            print('\t', interval)


if __name__ == '__main__':
    main()
