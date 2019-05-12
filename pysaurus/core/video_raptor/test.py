import sys

from pysaurus.core.video_raptor import api as video_raptor

def main():
    print('Hardware device(s):', ', '.join(video_raptor.get_hardware_device_names()))

    if len(sys.argv) != 2:
        return
    file_names = []
    with open(sys.argv[1], encoding='utf-8') as list_file:
        for line in list_file:
            line = line.strip()
            if line and line[0] != '#' and line not in file_names:
                file_names.append(line)
    if not file_names:
        return

    thumb_names = [str(file_index) for file_index in range(len(file_names))]
    info_output = video_raptor.collect_video_info(file_names)
    thumb_output = video_raptor.generate_video_thumbnails(file_names, thumb_names, '.')
    for i in range(len(file_names)):
        print(file_names[i])
        print(info_output[i])
        print(thumb_output[i])
        print()


if __name__ == '__main__':
    main()
