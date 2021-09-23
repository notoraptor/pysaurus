from pysaurus.core.components import AbsolutePath


def new_sub_file(folder: AbsolutePath, extension: str):
    return AbsolutePath.file_path(folder, folder.title, extension)


def new_sub_folder(folder: AbsolutePath, suffix: str, sep="."):
    return AbsolutePath.join(folder, f"{folder.title}{sep}{suffix}")
