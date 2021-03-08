from pysaurus.core.sebgui import HTML, seb_gui, file_path_to_url_path
import sys
from pysaurus.core.components import AbsolutePath
from typing import List, Tuple


class Interface:
    def __init__(self, duplicates: List[Tuple[AbsolutePath, List[AbsolutePath]]]):
        self._duplicates = duplicates
        self._gen = HTML(css="""
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
        """, javascript="""
        function check() {
            const form = document.forms["myform"];
            const keys = Object.keys(form);
            console.log(`Form content: ${keys.length}`);
        }
        """)

    def _img_to_html(self, dup_id, name, i, file_path):
        value = f"{dup_id}-{i}"
        return f"""
        <div class="item">
            <div class="image">
                <label for="{name}-{i}"><img src="{file_path_to_url_path(file_path.path)}" alt="Bad image"/></label>
            </div>
            <div class="title">
                <input id="{name}-{i}" type="radio" name="{name}" value="{value}" {"checked" if i == 0 else ""}/>
                <label for="{name}-{i}">{file_path.get_basename()}</label>
            </div>
        </div>
        """

    def _dup_to_html(self, dup_id, dup):
        dup_folder, dup_files = dup
        name = dup_folder.title
        img_strings = [self._img_to_html(dup_id, name, i, file_path) for i, file_path in enumerate(dup_files)]
        assert len(img_strings) == len(dup_files)
        return f"""
        <tr>
            <td class="folder">
                <input id="{name}-none" type="radio" name="{name}" value=""/>
                <label for="{name}-none">{name}</label>
            </td>
            <td><div class="items">{"".join(img_strings)}</div></td>
        </tr>
        """

    def index(self):
        dup_strings = [self._dup_to_html(i, dup) for i, dup in enumerate(self._duplicates)]
        assert len(dup_strings) == len(self._duplicates)
        return self._gen(
            f"""
            <h1>{len(self._duplicates)} duplicate(s)</h1>
            <form action="app://move" method="post" name="myform" onsubmit="return check()">
                <p>
                    Output folder:
                    <input type="text" name="output"/>
                    <input type="submit" value="send"/>
                </p>
                <table><tbody>
                {"".join(dup_strings)}
                </tbody></table>
            </form>
            """
        )

    def move(self, **kwargs):
        for k, v in kwargs.items():
            v = v.strip()
            print(k, '=', v)
            continue
            if not v:
                continue
            dup_id, file_id = v.split('-')
            dup = self._duplicates[int(dup_id)]
            fil = dup[1][int(file_id)]
            print(k, '=', dup[0], fil)
        print('K', len(kwargs), 'D', len(self._duplicates))
        return "Sent!"
        # assert len(kwargs) == len(self._duplicates) + 1, (len(kwargs), len(self._duplicates))
        # output = None
        # inputs = []
        # for k, v in kwargs.items():
        #     if v:
        #         path = AbsolutePath(v)
        #         if path.isfile():
        #             inputs.append(path)
        #         else:
        #             assert path.isdir() or not path.exists()
        #             assert k == "output", (k, v, path)
        #             output = path
        #     else:
        #         print('Skipped', k)
        # assert output
        # return f"Sent {len(inputs)} file(s) to move to: {output}"


def main():
    folder = AbsolutePath(r'G:\donnees\discord\ero-room\dupplicates')
    # if len(sys.argv) != 2:
    #     raise RuntimeError('Required a folder of duplicates.')
    # folder = AbsolutePath(sys.argv[1])
    if not folder.isdir():
        raise RuntimeError(f'Not a folder {folder}')
    duplicates = []
    for i, name in enumerate(folder.listdir()):
        dup_path = AbsolutePath.join(folder, name)
        files = []
        if not dup_path.isdir():
            raise RuntimeError(f'Not a sub-folder: {dup_path}')
        for sub_name in dup_path.listdir():
            file_path = AbsolutePath.join(dup_path, sub_name)
            if not file_path.isfile():
                raise RuntimeError(f'Not a sub-folder file: {file_path}')
            files.append(file_path)
        if len(files) > 1:
            duplicates.append((dup_path, files))
        if (i + 1) % 100 == 0:
            print('Loaded', i + 1)
    seb_gui("My Software!", Interface(duplicates))


if __name__ == "__main__":
    main()
