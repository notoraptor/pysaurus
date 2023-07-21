Video file manager written in Python (WIP).

```
ffprobe -v quiet -print_format json -show_format -show_streams "<video-file>" > "<output-file>.json"
```

# Abandoned:

- Using SQL instead of JSON could it make code faster and easier to maintain ?
  - No. It may speed up code to select sources, but I don't think it will help 
    when searching videos by terms.
- Qt player based on VLC is no longer available in interface. Moved into `other`
  - Qt player may freeze unexpectedly when requiring next video
  - We read some duration as a negative too big number, 
    while vlc detects real duration correctly.

# Done:

- video terms detection sometimes split words that contains uppercases,
  but those words should not be split.
  - E.g. "FiLM" must not be split in
    "Dragon Ball Z - FiLM x 01 - A la poursuite de Garlic MULTi 1080p BluRay x265 - KHAYA"
  - Partially solved: to built terms, we split both 
    default text and lowercase version of default text
  - E.g. for "FiLM", we will extract terms from both "FiLM" and "film"
- When opening grouping dialog and clicking to group button without anything else,
  grouping will not occurre (attribute is not selected by default)
- Remember entry edition and add an option to sort by date edited.
- Add an option "save to playlist" to save current view into a playlist.
- Keep history of opened videos. Maybe use a dynamic video property "date_opened".
- Error when deleting a database:
  - FileNotFoundError: [Errno 2] No such file or directory: '<database>.log'

# TODO:

## Bugs:

- Interface:
  - Does Database write on the right log file when deleting or changing database ?
  - top of centered text in fancy box is not shown if window is too small 
    (e.g. with form to confirm database deletion)
- Cannot force kill a Python thread.
- If selected videos are emptied, it prints "selected -1 /0"

## Features:

- Interface
  - Remember last edition panel selected for grouped property values
    (either delete, edit or move panel).
  - Redesign using bootstrap ?
  - Suggest existing values on property edition.
  - Add an option to execute a command line (example, `sort +date -length`)
    from interface, as a shortcut instead of multiple interface clicks.
    - Does that mean interface is not ergonomic?
- Allow user to add shortcuts (under Shift control, e.g. "Shift + N") to either:
  - edit a unique property
  - add a value to a multiple property
- Manage errors like read-only properties.
- Add video property "date_added" for date when video was added to database.
- Clean a multiple string property from another (unique/multiple) string property.
- Fill keywords from a specific string property to another multiple string property.
- Allow to add plugins as video context menu.
  - For each video, check if plugin is applicable. 
  - If so, add it as context menu (menu hierarchy, action for each menu)

## Optimizations:

- Memory leaks in python code when running gui ?
- Interface
  - Optimize video similarities algorithm
    - reduce size of allocated map (n**2 -> n*(n-1)/2)
- Interface update is too slow on video properties edition or group/classifier changes.
  - Database backup and terms index update needs to be optimized.
- Allow both to delete video or move video to trash
- As video is hashed using filename, filename attribute should be non-mutable.
  If we need to change filename (e.g. when renaming video), we should recreate
  a new video object copied from old one with necessary changes applied to new one.
- If provider is grouping w/rt a property, and this property is deleted in property page,
  provider is not currently updated.
- Moving files is very slow, especially for a large batch of moves.
  - Maybe open moving progression in a dedicated panel (homepage with progress bars) ?

Filter by
- source
  - all(flag is True for flag in flags_1) or all(flag is True for flag in flags_n)
- group by field
  - counter(video[field] for video in database)
  - sort counter by count, field, or field string length
- classify by path in group field
  - selection = (video for video in database if path in video[field])
  - counter(video[field] for video in selection)
- search
- sort
- select
