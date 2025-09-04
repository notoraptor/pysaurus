# Remarks for Linux

Tested on Linux (Ubuntu 20.04.6 LTS)

## Flet

Error:
```
flet: error while loading shared libraries: libmpv.so.1: cannot open shared object file
```
Fix:
```
sudo apt install libmpv1
```

## Qt / QWebEnginePage

Code:

```python
from PyQt6.QtWebEngineCore import QWebEnginePage
from pysaurus.core.absolute_path import AbsolutePath
```
Error:
```
ImportError: /home/stevenbocco/anaconda3/envs/pysaurus/lib/python3.12/lib-dynload/pyexpat.cpython-312-x86_64-linux-gnu.so: undefined symbol: XML_SetReparseDeferralEnabled
```
Fix:

Import QWebEnginePage after Pysaurus symbols

```python
from pysaurus.core.absolute_path import AbsolutePath
from PyQt6.QtWebEngineCore import QWebEnginePage
```

## Qt

Error:
```
Using fallback backend for videos info and thumbnails.
Using fallback backend for video similarities search.
qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

Available platform plugins are: linuxfb, wayland, wayland-egl, eglfs, vnc, minimal, xcb, vkkhrdisplay, offscreen, minimalegl.


Process finished with exit code 134 (interrupted by signal 6:SIGABRT)
```
Fix:
```
sudo apt install libxcb-cursor-dev
```

## Conclusion

It would be good to have a GUI framework who works out of the box with just Python packages,
without having to install any system dependencies.
