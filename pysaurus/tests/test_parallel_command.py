import sys
import subprocess
import multiprocessing
from pysaurus.core.functions import parallelize


def collect(*args):
    input_filename = r'C:\data\git\.local\videos.txt'
    output_filename = r'C:\data\git\.local\output.txt'
    process = subprocess.Popen(['runVideoRaptorBatch', input_filename, output_filename], stdout=subprocess.PIPE)
    for line in process.stdout.readlines():
        print('Got:', line.decode().strip())


def main():
    parallelize(collect, [None, None, None, None], 8)



if __name__ == '__main__':
    main()
