Video file manager written in Python (WIP).


```
ffprobe -v quiet -print_format json -show_format -show_streams "<video-file>" > "<output-file>.json"
```

TODO:
- Add possibility to change language. Minimum languages expected: english, french.Add
- Memory leak in python code when running gui ?
- Current important folders:
  - pysaurus/core
  - pysausur/interface/webtop
