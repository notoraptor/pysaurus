""""
Reduce size of videos which have extension ".mp4" in working directory.
Use ffmpeg for resizing. Resized videos is written in sub-folder "reduced"
(make sure this folder exists before running this script).
Video ratio (expected 16/9) is kept, height is resized to 270 pixels.
Make sure width and height can be divided by 270.

To use the script:
```
python reduce.py > script.sh	# or scipr.bat on Windows
./script.sh						# or `script.bat` on Windoed
# On Unix, you may need to make script.sh runnable before using it (`chmod u+x script.sh`).
```
"""
import os
paths = [name for name in os.listdir(".") if name.endswith(".mp4")]
for name in paths:
	print('ffmpeg -y -i %s -vf scale=-1:270 reduced/%s' % (name, name))
