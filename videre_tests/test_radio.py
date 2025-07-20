import videre


def test_radio(window_testing, image_testing, fake_user):
    radio1 = videre.Radio(value="one")
    radio2 = videre.Radio(value="two")
    radio3 = videre.Radio(value="three")
    text = videre.Text("none")

    def on_change(group: videre.RadioGroup):
        text.text = group.value

    group = videre.RadioGroup(
        videre.Column([radio1, radio2, radio3, text]), on_change=on_change
    )

    window_testing.controls = [group]
    window_testing.render()
    assert text.text == "none"

    fake_user.click(radio1)
    window_testing.render()
    assert text.text == "one"

    fake_user.click(radio2)
    window_testing.render()
    assert text.text == "two"

    fake_user.click(radio3)
    window_testing.render()
    assert text.text == "three"

    image_testing(window_testing.snapshot())
