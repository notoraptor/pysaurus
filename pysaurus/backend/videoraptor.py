import ujson as json
import subprocess
from pysaurus.utils.absolute_path import AbsolutePath


def videoraptor(list_file_path: AbsolutePath):
    videoraptor_path = 'C:\\donnees\\programmation\\git\\videoraptor\\.local\\videoraptor.exe'
    command = [videoraptor_path, list_file_path.path]
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None)
    std_out, std_err = p.communicate()
    # if std_err: raise Exception(std_err)
    return std_out
