from pysaurus.core.functions import class_get_public_attributes


class FakeVideo:
    """Wrapper to copy public Video fields (especially excluding database attribute)"""

    def __init__(self, video):
        fields = class_get_public_attributes(type(video))
        self.__dict__.update({field: getattr(video, field) for field in fields})
