Video file manager written in Python (WIP).

```
ffprobe -v quiet -print_format json -show_format -show_streams "<video-file>" > "<output-file>.json"
```

TODO:
- Add possibility to change language. Minimum languages expected: english, French.
- Memory leaks in python code when running gui ?
- Interface
  - Remember last property value edition panel selected (either delete, edit or move panel).
  - Using SQL instead of JSON could it make code faster and easier to maintain ?
  - Redesign using bootstrap ?
  - Suggest existing values on property edition.
  - Filter width may exceed allocated width, e.g. on unbreakable search term.
  - on database page, we need option to edit/delete existing databases.
  - Update group panel (bottom left) on property edition if group panel displays edited property.
  - Add an option to execute a command line (example, `sort +date -length`) from interface, as a shortcut instead of multiple interface clicks.
    - Does that mean interface is not ergonomic ?
