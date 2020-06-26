import subprocess

from pysaurus.core.functions import parallelize


def collect(*args):
    input_filename = r'C:\data\git\.local\videos.txt'
    output_filename = r'C:\data\git\.local\output.txt'
    process = subprocess.Popen(['runVideoRaptorBatch', input_filename, output_filename], stdout=subprocess.PIPE)
    for line in process.stdout.readlines():
        print('Got:', line.decode().strip())


def video_list_to_jsonl(input_file_name, output_file_name, job_id, job_count):
    process = subprocess.Popen(['runVideoRaptorBatch', input_file_name, output_file_name], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    for line in process.stdout.readlines():
        line = line.decode().strip()
        if line:
            if line.startswith('#'):
                pass
            else:
                step = int(line)


def main():
    parallelize(collect, [None, None, None, None], 8)


if __name__ == '__main__':
    main()
