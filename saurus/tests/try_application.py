from pysaurus.core.profiling import Profiler
from saurus.sql.application import Application

app = Application()
names = app.list_collections()
print("Collections:")
for name in names:
    print(f"\t{name}")
name = "adult videos"
print("Opening:", name)
with Profiler("open"):
    col = app.open_collection(name)
print("videos:", len(col.videos))
print("sources:", len(col.sources))
