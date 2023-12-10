from pysaurus.core.components import AbsolutePath, Date
from pysaurus.core.functions import coord_to_flat
from pysaurus.core.modules import ImageUtils
from pysaurus.core.profiling import Profiler


def merge_pixels(data, width, coordinates):
    indices = [coord_to_flat(x, y, width) for x, y in coordinates]
    return (
        round(sum(data[i][0] for i in indices) / len(indices)),
        round(sum(data[i][1] for i in indices) / len(indices)),
        round(sum(data[i][2] for i in indices) / len(indices)),
    )


def merge_pixels_2(data, width, position, coordinates):
    index = coord_to_flat(*position, width)
    indices = [coord_to_flat(x, y, width) for x, y in coordinates]
    indices.remove(index)
    r = round(
        255
        * (
            (data[index][0] + sum(data[i][0] ** 2 for i in indices))
            / (255 + (255**2) * len(indices))
        )
    )
    g = round(
        255
        * (
            (data[index][1] + sum(data[i][1] ** 2 for i in indices))
            / (255 + (255**2) * len(indices))
        )
    )
    b = round(
        255
        * (
            (data[index][2] + sum(data[i][2] ** 2 for i in indices))
            / (255 + (255**2) * len(indices))
        )
    )
    return r, g, b


def main():
    path = AbsolutePath(
        r"C:\Users\notoraptor-desktop\Downloads\medias\shiori izawa F3QHsUTbMAAgefV.jpg"
    )
    image = ImageUtils.open_rgb_image(path.path)
    width, height = image.size
    print(width, height)
    data = list(image.getdata())
    output = [None] * (width * height)
    with Profiler("Merge pixels"):
        for (x, y), fronts in ImageUtils.get_near_front_pixels(width, height):
            output[coord_to_flat(x, y, width)] = merge_pixels_2(
                data, width, (x, y), fronts
            )
    new_image = ImageUtils.new_rgb_image(output, width, height)
    new_image.save(f"ignored/average_{Date.now().time}.jpg")


if __name__ == "__main__":
    main()
