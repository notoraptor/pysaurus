import time
from types import SimpleNamespace

import videre


def test_animator_display(snap_win):
    text = videre.Text("Frame 0")
    animator = videre.Animator(text, fps=60)
    snap_win.controls = [animator]


def test_animator_frame_callback(fake_win):
    data = SimpleNamespace(frames=[], control_refs=[])

    def on_frame(control, frame_rank):
        data.frames.append(frame_rank)
        data.control_refs.append(control)

    text = videre.Text("Test")
    animator = videre.Animator(text, on_frame=on_frame, fps=60)
    fake_win.controls = [animator]

    assert animator.frame_rank == 0
    assert len(data.frames) == 0

    # Initial render
    fake_win.render()

    # Simulate frame updates by calling render() multiple times
    # This will trigger _check_fps and potentially increment frames
    for _ in range(10):
        time.sleep(0.01)
        fake_win.render()

    # At least one frame should have been processed
    assert animator.frame_rank >= 1
    assert len(data.frames) >= 1
    assert all(control is text for control in data.control_refs)


def test_animator_control_property(fake_win):
    text1 = videre.Text("Control 1")
    text2 = videre.Text("Control 2")

    animator = videre.Animator(text1, fps=30)
    fake_win.controls = [animator]
    fake_win.render()

    assert animator.control is text1

    # Change control
    animator.control = text2
    fake_win.render()

    assert animator.control is text2


def test_animator_fps_bounds(fake_win):
    text = videre.Text("Test")

    # Test negative fps
    animator1 = videre.Animator(text, fps=-10)
    assert animator1._fps == 0

    # Test very high fps (should be clamped to WINDOW_FPS)
    animator2 = videre.Animator(text, fps=1000)
    # Should be clamped to WINDOW_FPS (typically 60)
    assert animator2._fps <= 60

    # Test normal fps
    animator3 = videre.Animator(text, fps=30)
    assert animator3._fps == 30


def test_animator_on_frame_change(fake_win):
    data = SimpleNamespace(callback1_calls=0, callback2_calls=0)

    def callback1(control, frame_rank):
        data.callback1_calls += 1

    def callback2(control, frame_rank):
        data.callback2_calls += 1

    text = videre.Text("Test")
    animator = videre.Animator(text, on_frame=callback1, fps=60)
    fake_win.controls = [animator]
    fake_win.render()

    # Force a frame update
    time.sleep(0.1)
    fake_win.render()

    assert data.callback1_calls > 1
    assert data.callback2_calls == 0

    # Change callback
    animator.on_frame = callback2
    fake_win.render()

    # Force another frame update
    time.sleep(0.1)
    fake_win.render()

    assert data.callback1_calls > 1
    assert data.callback2_calls > 1


def test_animator_no_callback(fake_win):
    text = videre.Text("Test")
    animator = videre.Animator(text, on_frame=None, fps=60)
    fake_win.controls = [animator]

    # Should not crash without callback
    fake_win.render()

    time.sleep(0.1)
    fake_win.render()
