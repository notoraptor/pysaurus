Video file manager written in Python (WIP).


```
ffprobe -v quiet -print_format json -show_format -show_streams "<video-file>" > "<output-file>.json"
```

Current important folders:
- pysaurus/core
- pysausur/interface/webtop


TODO:
- Add possibility to change language. Minimum languages expected: english, french.Add
- Memory leak in python code when running gui ?
- Interface
  - Option to reverse classifier path or move up/down pah elements.
  - Remember last property value edition panel selected (either delete, edit or move panel).
  - Property navigation: on click on a property value in a video property panel, go to that property value (group by property then display videos with clicked value)
  - Option to edit properties for many videos at once (keep/generalize/add/remove propertiy values from selected videos)
  - Suggest existing values on property edition.
