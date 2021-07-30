import shutil

from pysaurus.core import notifications, functions
from pysaurus.core.components import AbsolutePath, FilePath, FileSize
from pysaurus.core.notifier import Notifier, DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler


class FileCopier:
    __slots__ = "cancel", "src", "dst", "buffer_size", "notifier", "total"

    def __init__(
        self,
        src: AbsolutePath,
        dst: AbsolutePath,
        *,
        buffer_size: int = 0,
        notifier: Notifier = DEFAULT_NOTIFIER,
    ):
        src = AbsolutePath.ensure(src)
        dst = AbsolutePath.ensure(dst)
        buffer_size = buffer_size or 32 * 1024 * 1024
        assert buffer_size > 0
        if not src.isfile():
            raise OSError(f"Source path does not exist: {src}")
        if dst.exists():
            raise OSError(f"Destination path already exists: {dst}")

        dst_dir = dst.get_directory()
        if not dst_dir.isdir():
            raise OSError(f"Destination folder does not exists: {dst_dir}")
        disk_usage = shutil.disk_usage(dst_dir.path)
        total = src.get_size()
        if total >= disk_usage.free:
            raise OSError(
                f"No enough free space on destination disk. "
                f"Required {FileSize(total)} ({total} o), "
                f"available {FileSize(disk_usage.free)} ({disk_usage.free} o)"
            )

        self.src = src
        self.dst = dst
        self.total = total
        self.buffer_size = buffer_size
        self.notifier = notifier
        self.cancel = False

    def copy(self):
        job_notifier = notifications.Jobs.copy_file(
            self.total, self.notifier, f"{FileSize(self.total)} to copy"
        )
        with Profiler("Copy", self.notifier):
            try:
                with open(self.src.path, "rb") as in_file:
                    with open(self.dst.path, "wb") as out_file:
                        size = 0
                        while not self.cancel:
                            buffer = in_file.read(self.buffer_size)
                            if not buffer:
                                break
                            size += out_file.write(buffer)
                            job_notifier.progress(None, size, self.total)
                if self.cancel:
                    self.dst.delete()
                else:
                    assert self.dst.isfile(), "Destination file does not exists"
                    assert (
                        self.total == self.dst.get_size() == size
                    ), "Copied file does not have same size as initial file"
            except Exception:
                self.dst.delete()
                raise
        if self.cancel:
            self.notifier.notify(notifications.Cancelled())
        else:
            self.notifier.notify(notifications.Done())
        return not self.cancel


def test(notifier=DEFAULT_NOTIFIER, run_shutil=True):
    src = AbsolutePath.join(functions.package_dir(), "..", ".local", "huge.txt")
    assert src.isfile()
    dst1 = FilePath(src.get_directory(), src.file_title, f"1.{src.extension}")
    dst2 = FilePath(src.get_directory(), src.file_title, f"2.{src.extension}")
    dst1.delete()
    dst2.delete()
    if run_shutil:
        with Profiler("shutil", notifier=notifier):
            shutil.copy(src.path, dst1.path)
    FileCopier(src, dst2, notifier=notifier).copy()


if __name__ == "__main__":
    test()
