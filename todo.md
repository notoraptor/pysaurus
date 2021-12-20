Video file manager written in Python (WIP).

```
ffprobe -v quiet -print_format json -show_format -show_streams "<video-file>" > "<output-file>.json"
```

> Using SQL instead of JSON could it make code faster and easier to maintain ?

No. It may speed up code to select sources, but I don't think it will help
when searching videos by terms.


TODO:

Bugs:
- Error when deleting a database:
  - FileNotFoundError: [Errno 2] No such file or directory: '<database>.log'
- Interface:
  - Does Database write on the right log file when deleting or changing database ?
  - top of centered text in fancy box is not shown if window is too small 
    (e.g. with form to confirm database deletion)
- Qt player may freeze unexpectedly when requiring next video
- Cannot force kill a Python thread.
- We read some duration as a negative too big number,
  while vlc detects real duration correctly.
- videos terms detection sometimes split words that contains uppercases, but those words should not be split.
  - E.g. "FiLM" must not be split in "Dragon Ball Z - FiLM x 01 - A la poursuite de Garlic MULTi 1080p BluRay x265 - KHAYA"
- If selected videos are emptied, it prints "selected -1 /0"

Features:
- Remember entry edition and add an option to sort by date edited.
- Interface
  - Remember last edition panel selected for grouped property values
    (either delete, edit or move panel).
  - Redesign using bootstrap ?
  - Suggest existing values on property edition.
  - Add an option to execute a command line (example, `sort +date -length`)
    from interface, as a shortcut instead of multiple interface clicks.
    - Does that mean interface is not ergonomic?
- Allow user to add shortcuts (under Shift control, e.g. "Shift + N") to either:
  - set a unique property
  - add a value to a multiple property
- Add an option "save to playlist" to save current view into a playlist.

Optimizations:
- Memory leaks in python code when running gui ?
- Interface
  - Optimize video similarities algorithm
    - reduce size of allocated map (n**2 -> n*(n-1)/2)
- Interface update is too slow on video properties edition or group/classifier changes.
  - Database backup and terms index update needs to be optimized.
