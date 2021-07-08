Video file manager written in Python (WIP).


```
ffprobe -v quiet -print_format json -show_format -show_streams "<video-file>" > "<output-file>.json"
```

Current important folders:
- pysaurus/core
- pysausur/interface/webtop


TODO:
- Add possibility to change language. Minimum languages expected: english, French.
- Memory leaks in python code when running gui ?
- Interface
  - Remember last property value edition panel selected (either delete, edit or move panel).
  - Speed-up code, especially database (re)loading.
  - We need to check if video exists only on database (re)loading, but nowhere else.
  - Using SQL instead of JSON could it make code faster and easier to maintain ?
  - Redesign using bootstrap ?
  - Suggest existing values on property edition.
  - Filter width may exceed allocated width, e.g. on unbreakable search term.
  - Add new pages at start to choose/edit/delete/create many databases.
  - Update group panel (bottom left) on property edition if group panel displays edited property.
  - Auto-scroll down database loading panel (in homepage).
  - Add an option to execute a command line (example, `sort +date -length`) from interface, as a shortcut instead of multiple interface clicks.
    - Does that mean interface is not ergonomic ?
