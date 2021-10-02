Video file manager written in Python (WIP).

```
ffprobe -v quiet -print_format json -show_format -show_streams "<video-file>" > "<output-file>.json"
```

> Using SQL instead of JSON could it make code faster and easier to maintain ?

No. It may speed up code to select sources, but I don't think it will help
when searching videos by terms.


TODO:

Features:
- Add possibility to change language. Minimum languages expected: English, French.
- Interface
  - Remember last edition panel selected for grouped property values
    (either delete, edit or move panel).
  - Redesign using bootstrap ?
  - Suggest existing values on property edition.
  - Add an option to execute a command line (example, `sort +date -length`)
    from interface, as a shortcut instead of multiple interface clicks.
    - Does that mean interface is not ergonomic?

Optimizations:
- Memory leaks in python code when running gui ?
- Interface
  - Optimize video similarities algorithm
    - reduce size of allocated map (n**2 -> n*(n-1)/2)
- Interface update is too slow on video properties edition or group/classifier changes.
  - Database backup and terms index update needs to be optimized.
