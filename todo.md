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
  - Add an option to execute a command line (example, `sort +date -length`) from interface, as a shortcut instead of multiple interface clicks.
    - Does that mean interface is not ergonomic ?
  - Make sure video menu is atop of everything.
  - When grouping videos, display same or different values with specific color.
  - group paging is not updated if last page is emptied
  - some attributes could not be used to sort (e.g. "moved files (potentially)")
