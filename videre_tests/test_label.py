import videre


def test_label(fake_win, fake_user):
    checkbox = videre.Checkbox()
    label = videre.Label(checkbox, text="control checkbox!", height_delta=0)
    fake_win.controls = [
        videre.Row([label, videre.Container(checkbox, padding=videre.Padding(left=10))])
    ]
    fake_win.check("r0")
    assert not checkbox.checked

    fake_user.click(label)
    fake_win.check("r1")
    assert checkbox.checked


def test_label_with_key(fake_win, fake_user):
    key = "my_checkbox"
    checkbox = videre.Checkbox(key=key)
    label = videre.Label(key, text="control checkbox!", height_delta=0)
    fake_win.controls = [
        videre.Row([label, videre.Container(checkbox, padding=videre.Padding(left=10))])
    ]
    fake_win.check("r0")
    assert not checkbox.checked

    fake_user.click(label)
    fake_win.check("r1")
    assert checkbox.checked
