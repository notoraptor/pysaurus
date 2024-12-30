import os

IMAGE_EXAMPLE = os.path.join(os.path.dirname(__file__), "flowers-7660120_640.jpg")
assert os.path.isfile(IMAGE_EXAMPLE)
