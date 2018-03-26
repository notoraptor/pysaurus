def _print_duplicates(collection_list):
    basename_to_paths = {}
    for path in collection_list:  # type: AbsolutePath
        if path.basename not in basename_to_paths:
            basename_to_paths[path.basename] = {path}
        else:
            basename_to_paths[path.basename].add(path)
    print(len(basename_to_paths), 'titles. Possible duplicates:')
    for basename, path_set in basename_to_paths.items():
        if len(path_set) > 1:
            size_to_paths = {}
            for path in path_set:
                size = path.get_size()
                if size not in size_to_paths:
                    size_to_paths[size] = {path}
                else:
                    size_to_paths[size].add(path)
            if any(len(p) > 1 for p in size_to_paths.values()):
                print(basename)
            for size, paths in size_to_paths.items():
                if len(paths) > 1:
                    for path in paths:  # type: AbsolutePath
                        print('\t', path.get_size(), '\t"', path, '"', sep='')
