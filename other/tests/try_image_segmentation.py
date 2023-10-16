from pysaurus.core.classes import AbstractMatrix
from pysaurus.core.components import AbsolutePath, Date
from pysaurus.core.display import Display
from pysaurus.core.modules import ImageUtils
from pysaurus.core.profiling import Profiler
from pysaurus.miniature.group_computer import GroupComputer


class PysaurusImage(AbstractMatrix):
    __slots__ = ("image",)

    def __init__(self, *, path: AbsolutePath = None, image=None):
        assert (image is not None) ^ (path is not None)
        self.image = image or ImageUtils.open_rgb_image(path.path)
        super().__init__(*self.image.size)

    def data(self):
        return self.image.getdata()


def main():
    path = AbsolutePath(
        r"C:\Users\notoraptor-desktop\Downloads\medias\shiori izawa F3QHsUTbMAAgefV.jpg"
    )
    group_min_size = 0  # 0
    pixel_distance_radius = 5  # 6
    normalizer = 0
    group_computer = GroupComputer(
        group_min_size=group_min_size,
        pixel_distance_radius=pixel_distance_radius,
        normalizer=normalizer,
    )
    image = PysaurusImage(path=path)

    with Profiler("group pixels"):
        groups = group_computer.group_pixels(image)
    output = [(0, 0, 0)] * (image.width * image.height)
    with Profiler("generate output"):
        for group in groups:
            for index in group.members:
                output[index] = tuple(int(v) for v in group.color)
    with Profiler("generate new image"):
        new_image = ImageUtils.new_rgb_image(output, image.width, image.height)

    new_image.save(
        f"ignored/r{pixel_distance_radius}_n{normalizer}_t{Date.now().time}.jpg"
    )
    new_image.thumbnail((300, 300))
    Display.from_images(new_image)


if __name__ == "__main__":
    with Profiler("script"):
        main()
