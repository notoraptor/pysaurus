class VideoInterval:
    def __init__(self, fields):
        self.fields = tuple(fields)
        self.min = {}
        self.max = {}

    def update(self, videos):
        self.min.clear()
        self.max.clear()
        if not isinstance(videos, list):
            videos = list(videos)
        if not videos:
            return
        for field in self.fields:
            min_value = getattr(videos[0], field)
            max_value = min_value
            for i in range(1, len(videos)):
                value = getattr(videos[i], field)
                if value < min_value:
                    min_value = value
                if value > max_value:
                    max_value = value
            self.min[field] = min_value
            self.max[field] = max_value
            # print('BOUNDS', field, min_value, max_value)
