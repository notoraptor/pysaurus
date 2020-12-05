import tkinter as tk

from PIL import ImageTk

from pysaurus.core import functions
from pysaurus.core.modules import ImageUtils


def dilate_data(data, width, height, factor: int):
    assert factor > 1
    output = []
    for row in range(height):
        line = []
        for col in range(width):
            pixel = data[functions.coord_to_flat(col, row, width)]
            line.extend(pixel for _ in range(factor))
        for _ in range(factor):
            output.extend(line)
    return output


def dilate_miniature_data(data: list, width: int, height: int):
    assert width == height == 32
    output = dilate_data(data, width, height, 4)
    assert len(output) == 128 * 128
    return output


class Draw:

    def __init__(self, width, height, background=(0, 0, 0)):
        self.surface = [background] * width * height
        self.width = width
        self.height = height
        self.background = background

    def resize(self, width, height, background=None):
        new_surface = [(background or self.background)] * width * height
        end_x = min(width, self.width)
        end_y = min(height, self.height)
        for x in range(end_x):
            for y in range(end_y):
                new_surface[functions.coord_to_flat(x, y, width)] = self.surface[
                    functions.coord_to_flat(x, y, self.width)]
        self.surface = new_surface
        self.width = width
        self.height = height
        self.background = background or self.background

    def draw_data(self, data, width, height, x, y):
        end_x = min(x + width, self.width)
        end_y = min(y + height, self.height)
        for i in range(x, end_x):
            for j in range(y, end_y):
                self.surface[functions.coord_to_flat(i, j, self.width)] = data[
                    functions.coord_to_flat(i - x, j - y, width)]

    def draw_image(self, image, x, y):
        assert image.mode == ImageUtils.IMAGE_RGB_MODE
        data = list(image.getdata())
        width, height = image.size
        return self.draw_data(data, width, height, x, y)

    def display(self):
        root = tk.Tk()
        image = ImageUtils.new_rgb_image(self.surface, self.width, self.height)
        tk_image = ImageTk.PhotoImage(image)
        label = tk.Label(master=root)
        label["image"] = tk_image
        label.pack(side="left")
        root.mainloop()
