import io

import pytest


@pytest.fixture
def image_testing(image_regression):
    def check(image: io.BytesIO):
        image_regression.check(image.getvalue(), diff_threshold=0)

    return check
