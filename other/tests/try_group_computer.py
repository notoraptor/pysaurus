from other.toolsaurus.modules import Display
from pysaurus.core.classes import AbstractMatrix
from pysaurus.core.components import AbsolutePath
from pysaurus.core.modules import ImageUtils
from pysaurus.core.profiling import Profiler
from pysaurus.database.db_settings import DbSettings
from pysaurus.miniature.group_computer import GroupComputer


class PysaurusImage(AbstractMatrix):
    __slots__ = ("image",)

    def __init__(self, path: AbsolutePath):
        self.image = ImageUtils.open_rgb_image(path.path)
        width, height = self.image.size
        super().__init__(width, height)

    def data(self):
        return self.image.getdata()


def main():
    path1 = AbsolutePath(
        r"C:\Users\notoraptor-desktop\Pictures\vlcsnap-2023-04-22-20h46m26s235.png"
    )
    path2 = AbsolutePath(
        r"C:\Users\notoraptor-desktop\Pictures\vlcsnap-2023-04-22-21h09m19s886.png"
    )
    path3 = AbsolutePath(
        r"C:\Users\notoraptor-desktop\Pictures\vlcsnap-2023-04-22-21h11m32s369.png"
    )
    path = path3
    settings = DbSettings()
    group_computer = GroupComputer(
        group_min_size=settings.miniature_group_min_size,
        pixel_distance_radius=settings.miniature_pixel_distance_radius,
    )
    image = PysaurusImage(path)
    with Profiler("group pixels"):
        groups = group_computer.group_pixels(image)
    output = [(0, 0, 0)] * (image.width * image.height)
    with Profiler("generate output"):
        for group in groups:
            color = tuple(int(v) for v in group.color)
            for index in group.members:
                output[index] = color
    with Profiler("generate new image"):
        new_image = ImageUtils.new_rgb_image(output, image.width, image.height)
    Display.from_images(new_image)


if __name__ == "__main__":
    main()
