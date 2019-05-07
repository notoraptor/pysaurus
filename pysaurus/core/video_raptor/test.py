import sys

from pysaurus.core.video_raptor.api import (get_hardware_device_names, collect_video_info, generate_video_thumbnails)


def main():
    print('Hardware device(s):', ', '.join(get_hardware_device_names()))

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

    filename_dictionary = {file_name: None for file_name in file_names}
    file_name_to_thumb_name = {file_name: str(file_index) for file_index, file_name in
                               enumerate(filename_dictionary.keys())}
    collect_video_info(filename_dictionary)
    generate_video_thumbnails(file_name_to_thumb_name, '.')
    for file_name, result in filename_dictionary.items():
        print(file_name)
        print(result)
        print(file_name_to_thumb_name[file_name])
        print()


if __name__ == '__main__':
    main()
