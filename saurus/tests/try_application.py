from pysaurus.core.profiling import Profiler
from saurus.sql.application import Application

app = Application()
names = app.list_collections()
print("Collections:", names)
print("Opening:", names[0])
with Profiler("open"):
    col = app.open_collection(names[0])
print(len(col.videos))
