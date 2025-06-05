import videre
from videre.widgets.abstractanimation import FPR


def test_progressing(window_testing, image_testing, request):
    print()
    window_testing.controls = [videre.Progressing(framing=FPR(1), steps=4)]
    # forward
    image_testing(window_testing.snapshot(), basename=f"{request.node.name}_r0")
    image_testing(window_testing.snapshot(), basename=f"{request.node.name}_r1")
    image_testing(window_testing.snapshot(), basename=f"{request.node.name}_r2")
    image_testing(window_testing.snapshot(), basename=f"{request.node.name}_r3")
    image_testing(window_testing.snapshot(), basename=f"{request.node.name}_r4")
    # backward
    image_testing(window_testing.snapshot(), basename=f"{request.node.name}_r5")
    image_testing(window_testing.snapshot(), basename=f"{request.node.name}_r6")
    image_testing(window_testing.snapshot(), basename=f"{request.node.name}_r7")
    image_testing(window_testing.snapshot(), basename=f"{request.node.name}_r8")
    # forward again
    image_testing(window_testing.snapshot(), basename=f"{request.node.name}_r9")
