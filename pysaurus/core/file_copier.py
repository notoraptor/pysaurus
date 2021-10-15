import shutil

from pysaurus.core import core_exceptions, job_notifications, notifications
from pysaurus.core.components import AbsolutePath, FileSize
from pysaurus.core.modules import FileSystem
from pysaurus.core.notifier import DEFAULT_NOTIFIER, Notifier


class FileCopier:
    __slots__ = "cancel", "src", "dst", "buffer_size", "notifier", "total", "notify_end"

    def __init__(
        self,
        src: AbsolutePath,
        dst: AbsolutePath,
        *,
        buffer_size: int = 0,
        notifier: Notifier = DEFAULT_NOTIFIER,
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
        self.notifier = notifier
        self.cancel = False
        self.notify_end = notify_end

    def move(self):
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
            ret = self.copy()
        if ret:
            src_stat = FileSystem.stat(self.src.path)
            FileSystem.utime(self.dst.path, (src_stat.st_atime, src_stat.st_mtime))
        return ret

    def copy(self):
        job_notifier = job_notifications.CopyFile(
            self.total, self.notifier, pretty_total=FileSize(self.total)
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
                        job_notifier.progress(
                            None, size, self.total, title=str(FileSize(size))
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
