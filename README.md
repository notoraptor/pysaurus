Video file manager written in Python (WIP).


```
ffprobe -v quiet -print_format json -show_format -show_streams "<video-file>" > "<output-file>.json"
```

Current important folders:
- pysaurus/core
- pysausur/interface/webtop


TODO:
- Make video indices (video_id) more stable
- Interface
  - Option to edit properties for many videos at once (keep/generalize/add/remove propertiy values from selected videos)
  - When search terms, check videos properties too
  - Option to reverse classifier path or move up/down pah elements.
  - Remember last property value edition panel selected (either delete, edit or move panel).
  - Property navigation: on click on a property value in a video property panel, go to that property value (group by property then display videos with clicked value)
  - Speed-up code, especially database (re)loading.
  - We need to check if video exists only on database (re)loading, but nowhere else.
  - Using SQL instead of JSON could it make code faster and easier to maintain ?
  - Redesign using bootstrap ?
  - Suggest existing values on property edition.
  - Filter width may exceed allocated width, e.g. on unbreakable search term.
  - Add new pages when program opens to choose/edit/delete/create many databases.
  - Update group panel (bottom left) on property edition if group panel displays edited property.
  - Auto-scroll down database loading panel.
- Add possibility to change language. Minimum languages expected: english, french.
- Memory leak in python code when running gui ?
