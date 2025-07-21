import videre


def test_radio(fake_win, fake_user):
    radio1 = videre.Radio(value="one")
    radio2 = videre.Radio(value="two")
    radio3 = videre.Radio(value="three")
    text = videre.Text("none")

    def on_change(group: videre.RadioGroup):
        text.text = group.value

    group = videre.RadioGroup(
        videre.Column([radio1, radio2, radio3, text]), on_change=on_change
    )

    fake_win.controls = [group]
    fake_win.render()
    assert text.text == "none"

    fake_user.click(radio1)
    fake_win.render()
    assert text.text == "one"

    fake_user.click(radio2)
    fake_win.render()
    assert text.text == "two"

    fake_user.click(radio3)
    fake_win.render()
    assert text.text == "three"

    fake_win.check()
