import os
import shutil

from pysaurus.core import notifications
from pysaurus.core.components import AbsolutePath, FileSize
from pysaurus.core.modules import FileSystem
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

    def move(self):
        src_drive = self.src.get_drive_name()
        dst_drive = self.dst.get_drive_name()
        if src_drive and dst_drive and src_drive == dst_drive:
            os.rename(self.src.path, self.dst.path)
            if self.src.exists():
                raise OSError("Move failed on same disk.")
            if not self.dst.isfile():
                raise OSError("Destination file not found after moving on same disk.")
            self.notifier.notify(notifications.Done())
            ret = True
        else:
            ret = self.copy()
        if ret:
            src_stat = FileSystem.stat(self.src.path)
            FileSystem.utime(self.dst.path, (src_stat.st_atime, src_stat.st_mtime))
        return ret

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
