import shutil

from pysaurus.core import core_exceptions, notifications
from pysaurus.core.components import AbsolutePath, FileSize
from pysaurus.core.informer import Informer
from pysaurus.core.modules import FileSystem


class FileCopier:
    __slots__ = (
        "cancel",
        "src",
        "dst",
        "buffer_size",
        "notifier",
        "total",
        "notify_end",
        "terminated",
    )

    def __init__(
        self,
        src: AbsolutePath,
        dst: AbsolutePath,
        *,
        buffer_size: int = 0,
        notify_end: bool = True,
    ):
        src = AbsolutePath.ensure(src)
        dst = AbsolutePath.ensure(dst)
        buffer_size = buffer_size or 32 * 1024 * 1024
        assert buffer_size > 0
        if not src.isfile():
            raise core_exceptions.NotAFileError(src)
        if dst.exists():
            raise FileExistsError(dst)

        dst_dir = dst.get_directory()
        if not dst_dir.isdir():
            raise NotADirectoryError(dst_dir)
        disk_usage = shutil.disk_usage(dst_dir.path)
        total = src.get_size()
        if total >= disk_usage.free:
            raise core_exceptions.DiskSpaceError(total, disk_usage.free)

        self.src = src
        self.dst = dst
        self.total = total
        self.buffer_size = buffer_size
        self.notifier = Informer.default()
        self.cancel = False
        self.notify_end = notify_end
        self.terminated = False

    def move(self):
        try:
            src_stat = FileSystem.stat(self.src.path)
            src_drive = self.src.get_drive_name()
            dst_drive = self.dst.get_drive_name()
            if src_drive and dst_drive and src_drive == dst_drive:
                FileSystem.rename(self.src.path, self.dst.path)
                if self.src.exists():
                    raise FileExistsError(self.src)
                if not self.dst.isfile():
                    raise core_exceptions.NotAFileError(self.dst)
                if self.notify_end:
                    self.notifier.notify(notifications.Done())
                ret = True
            else:
                ret = self.copy_file()
            if ret:
                FileSystem.utime(self.dst.path, (src_stat.st_atime, src_stat.st_mtime))
            return ret
        finally:
            self.terminated = True

    def copy_file(self):
        self.notifier.task(
            self.copy_file, self.total, "bytes", expectation=FileSize(self.total)
        )
        try:
            with open(self.src.path, "rb") as in_file:
                with open(self.dst.path, "wb") as out_file:
                    size = 0
                    while not self.cancel:
                        buffer = in_file.read(self.buffer_size)
                        if not buffer:
                            break
                        size += out_file.write(buffer)
                        self.notifier.progress(
                            self.copy_file, size, self.total, title=str(FileSize(size))
                        )
            if self.cancel:
                self.dst.delete()
            else:
                assert self.dst.isfile()
                assert self.total == self.dst.get_size() == size
        except Exception:
            self.dst.delete()
            raise
        if self.notify_end:
            if self.cancel:
                self.notifier.notify(notifications.Cancelled())
            else:
                self.notifier.notify(notifications.Done())
        return not self.cancel
