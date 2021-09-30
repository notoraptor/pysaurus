Video file manager written in Python (WIP).

```
ffprobe -v quiet -print_format json -show_format -show_streams "<video-file>" > "<output-file>.json"
```

> Using SQL instead of JSON could it make code faster and easier to maintain ?

No. It may speed up code to select sources, but I don't think it will help
when searching videos by terms.


TODO:
- Add possibility to change language. Minimum languages expected: English, French.
- Memory leaks in python code when running gui ?
- Interface
  - Remember last edition panel selected for grouped property values
    (either delete, edit or move panel).
  - Redesign using bootstrap ?
  - Suggest existing values on property edition.
  - Add an option to execute a command line (example, `sort +date -length`)
    from interface, as a shortcut instead of multiple interface clicks.
    - Does that mean interface is not ergonomic?
  - When grouping videos, display same or different values with specific color.
  - Optimize video similarities algorithm
    - reduce size of allocated map (n**2 -> n*(n-1)/2)
    - Maybe memorize list of coordinates to check after native comparison,
      instead of checking all potential positions.
  - Qt
    - Make sure video menu is atop of everything.
