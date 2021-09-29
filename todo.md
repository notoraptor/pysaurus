Video file manager written in Python (WIP).

```
ffprobe -v quiet -print_format json -show_format -show_streams "<video-file>" > "<output-file>.json"
```

> Using SQL instead of JSON could it make code faster and easier to maintain ?

No. It may speed up code to select sources, but I don't hink it will help
when searching videos by term, for e.g.


TODO:
- Add possibility to change language. Minimum languages expected: english, French.
- Memory leaks in python code when running gui ?
- Interface
  - Remember last property value edition panel selected (either delete, edit or move panel).
  - Redesign using bootstrap ?
  - Suggest existing values on property edition.
  - Add an option to execute a command line (example, `sort +date -length`)
    from interface, as a shortcut instead of multiple interface clicks.
    - Does that mean interface is not ergonomic?
  - When grouping videos, display same or different values with specific color.
  - some attributes must not be available for sorting (e.g. "moved files (potentially)")
  - Qt
    - Make sure video menu is atop of everything.
    - group paging is not updated if last page is emptied.
