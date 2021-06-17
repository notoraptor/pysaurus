def _clip_color(value):
    return min(max(0, value), 255)


def equalize(data):
    if not isinstance(data, (list, tuple)):
        data = list(data)
    grays = sorted({int(sum(p) / 3) for p in data})
    if len(grays) < 2:
        return data
    best_distance = 255 / (len(grays) - 1)
    new_grays = [0]
    for i in range(1, len(grays)):
        new_grays.append(new_grays[i - 1] + best_distance)
    new_grays = [round(gray) for gray in new_grays]
    assert new_grays[-1] == 255, new_grays[-1]
    gray_to_index = {gray: index for index, gray in enumerate(grays)}
    output = []
    for pixel in data:
        r, g, b = pixel
        gray = int((r + g + b) / 3)
        index = gray_to_index[gray]
        new_gray = new_grays[index]
        distance = new_gray - gray
        new_color = _clip_color(r + distance), _clip_color(g + distance), _clip_color(b + distance)
        # assert int(sum(new_color) / 3) == new_gray, (int(sum(new_color) / 3), new_gray, gray, new_color, pixel)
        output.append(new_color)
    return output
