from pysaurus.scripts.sebgui import HTML, convert_file_path_to_url
from pysaurus.scripts.webgui import web_gui
import os
from pysaurus.core.components import AbsolutePath
from typing import List, Tuple


class Interface:
    def __init__(self, duplicates: List[Tuple[AbsolutePath, List[AbsolutePath]]]):
        self._duplicates = duplicates
        self.dup_names = {
            dup_path.title: dup_files for dup_path, dup_files in self._duplicates
        }
        assert "output" not in self.dup_names
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
                <label for="{name}-{i}"><img src="{convert_file_path_to_url(file_path.path)}"/></label>
            </div>
            <div class="title">
                <input id="{name}-{i}" type="radio" name="{name}" value="{i}" {"checked" if i == 0 else ""}/>
                <label for="{name}-{i}">{file_path.get_basename()}</label>
            </div>
        </div>
        """

    def _dup_to_html(self, dup):
        dup_folder, dup_files = dup
        name = dup_folder.title
        return f"""
        <tr>
            <td class="folder">
                <input id="{name}-none" type="radio" name="{name}" value="-1"/>
                <label for="{name}-none">{name}</label>
            </td>
            <td><div class="items">{"".join(self._img_to_html(name, i, file_path) for i, file_path in enumerate(dup_files))}</div></td>
        </tr>
        """

    def index(self):
        # path = AbsolutePath.join(os.path.dirname(__file__), 'miwa.jpg')
        html = self._gen(
            f"""
            <h1>{len(self._duplicates)} duplicate(s)</h1>
            <form method="post" onsubmit="return webview_submit(this)">
                <p>
                    Output folder:
                    <input type="text" name="output" value="G:\donnees\discord\ero-room\images dédoublées\moved"/>
                    <input type="submit" value="send"/>
                </p>
                <table><tbody>
                {"".join(self._dup_to_html(dup) for i, dup in enumerate(self._duplicates))}
                </tbody></table>
            </form>
            """
        )
        return html

    def move(self, kwargs):
        assert len(kwargs) == len(self._duplicates) + 1, (
            len(kwargs),
            len(self._duplicates),
        )
        output = None
        inputs = []
        nb_dups_found = 0
        for k, v in kwargs.items():
            pass
        for k, v in kwargs.items():
            v = v.strip()
            if k == "output":
                assert output is None, output
                if not v:
                    return "No output provided"
                output = AbsolutePath(v)
                assert output.isdir() or not output.exists()
            else:
                assert k in self.dup_names, k
                nb_dups_found += 1
                index_file = int(v)
                if index_file != -1:
                    inputs.append(self.dup_names[k][index_file])
                    print("Found", k, v, index_file, self.dup_names[k][index_file])
        assert output
        return f"Sent {len(inputs)} file(s) to move to: {output}"


def main():
    folder = AbsolutePath(r"G:\donnees\discord\ero-room\dupplicates")
    # if len(sys.argv) != 2:
    #     raise RuntimeError('Required a folder of duplicates.')
    # folder = AbsolutePath(sys.argv[1])
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
        if (i + 1) % 10 == 0:
            break
        if (i + 1) % 100 == 0:
            print("Loaded", i + 1)

    print(os.getcwd())
    web_gui("My Software!", Interface(duplicates))


if __name__ == "__main__":
    main()