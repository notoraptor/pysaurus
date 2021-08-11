import os
from typing import List, Tuple

from pysaurus.core.components import AbsolutePath
from pysaurus.core.profiling import Profiler
from pysaurus.other.utils.servergui import HTML, FlaskInterface, flask_gui


class Interface(FlaskInterface):
    def __init__(self, duplicates: List[Tuple[AbsolutePath, List[AbsolutePath]]]):
        self._duplicates = duplicates
        self.dup_names = {
            dup_path.title: dup_files for dup_path, dup_files in self._duplicates
        }
        self.output_name = "output"
        i = 0
        while self.output_name in self.dup_names:
            self.output_name = f"output-{i}"
            i += 1
        self._gen = HTML(
            css="""
        body {
            font-family: Verdana, sans-serif;
        }
        .items {
            display: flex;
            flex-direction: row;
            /* flex-wrap: wrap; */
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .item {
            margin-left: 1rem;
            background-color: rgb(250, 250, 250);
            border-radius: 5px;
            padding: 5px;
        }
        img {
            max-height: 100px;
        }
        td {
            vertical-align: top;
        }
        td.folder, .item .title {
            white-space: nowrap;
        }
        .item .title {
            font-size: 0.75rem;
        }
        """
        )

    def _img_to_html(self, name, i, file_path):
        return f"""
        <div class="item">
            <div class="image">
                <label for="{name}-{i}">
                <img src="{self.backend_url(self.file, path=file_path.path)}"/>
                </label>
            </div>
            <div class="title">
                <input id="{name}-{i}" 
                       type="radio" 
                       name="{name}" 
                       value="{i}" 
                       {"checked" if i == 0 else ""}/>
                <label for="{name}-{i}">{file_path.get_basename()}</label>
            </div>
        </div>
        """

    def _dup_to_html(self, dup_id, dup):
        dup_folder, dup_files = dup
        name = dup_folder.title
        return f"""
        <tr>
            <td class="folder">
                <input id="{name}-none" type="radio" name="{name}" value="-1"/>
                <label for="{name}-none">{name}</label>
            </td>
            <td>
                <div class="items">
                    {"".join(
            self._img_to_html(name, i, file_path)
            for i, file_path in enumerate(dup_files)
        )}
                </div>
            </td>
        </tr>
        """

    def index(self):
        return self._gen(
            f"""
            <h1>{len(self._duplicates)} duplicate(s)</h1>
            <form method="post" action="{self.backend_url(self.move)}">
                <p>
                    Output folder:
                    <input type="text" 
                           name="{self.output_name}" 
                           value="G:\donnees\discord\ero-room\images dédoublées\moved"/>
                    <input type="submit" value="send"/>
                </p>
                <table><tbody>
                {"".join(
                self._dup_to_html(i, dup) for i, dup in enumerate(self._duplicates)
            )}
                </tbody></table>
                <p>
                    <input type="submit" value="send"/>
                </p>
            </form>
            <p>&nbsp;</p>
            """
        )

    def move(self, **kwargs):
        assert self.output_name in kwargs
        inputs = []  # type: List[AbsolutePath]
        output = kwargs.pop(self.output_name).strip()
        if not output:
            return (
                f"No output specified! "
                f'<a href="{self.backend_url(self.index)}">Back!</a>'
            )
        output = AbsolutePath(output)
        if not output.isdir() and output.exists():
            return (
                f"Not a directory and already exists: {output}. "
                f'<a href="{self.backend_url(self.index)}">Back!</a>'
            )
        assert len(kwargs) == len(self._duplicates), (
            len(kwargs),
            len(self._duplicates),
        )
        for k, v in kwargs.items():
            assert k in self.dup_names, k
            index_file = int(v.strip())
            if index_file != -1:
                inputs.append(self.dup_names[k][index_file])
                print("Found", k, index_file, self.dup_names[k][index_file])

        if not output.isdir():
            output.mkdir()
        movements = []
        with Profiler("Create movements"):
            for inp in inputs:
                new_file_path = AbsolutePath.join(output, inp.get_basename())
                movements.append((inp, new_file_path))
        with Profiler("Move files"):
            for i, (inp, out) in enumerate(movements):
                os.rename(inp.path, out.path)
                assert not inp.exists()
                assert out.isfile()
                if (i + 1) % 100 == 0:
                    print("Moved", i + 1)
        return f"Sent {len(inputs)} file(s) to: {output}"


def main():
    # if len(sys.argv) != 2:
    #     raise RuntimeError('Required a folder of duplicates.')
    # folder = AbsolutePath(sys.argv[1])
    folder = AbsolutePath(r"G:\donnees\discord\ero-room\duplicates")

    # Load folder of duplicates.
    if not folder.isdir():
        raise RuntimeError(f"Not a folder {folder}")
    duplicates = []
    for i, name in enumerate(folder.listdir()):
        dup_path = AbsolutePath.join(folder, name)
        files = []
        if not dup_path.isdir():
            raise RuntimeError(f"Not a sub-folder: {dup_path}")
        for sub_name in dup_path.listdir():
            file_path = AbsolutePath.join(dup_path, sub_name)
            if not file_path.isfile():
                raise RuntimeError(f"Not a sub-folder file: {file_path}")
            files.append(file_path)
        if len(files) > 1:
            duplicates.append((dup_path, files))
        # if (i + 1) % 10 == 0:
        #     break
        if (i + 1) % 100 == 0:
            print("Loaded", i + 1)

    # Load interface.
    interface = Interface(duplicates)
    flask_gui(interface, title="Duplicates")


if __name__ == "__main__":
    main()
