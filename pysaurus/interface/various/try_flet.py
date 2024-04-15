import flet as ft
import vlc

print(vlc)


def main(page: ft.Page):
    page.title = "Flet counter example"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    txt_number = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, width=100)

    def minus_click(e):
        txt_number.value = str(int(txt_number.value) - 1)
        page.update()

    def plus_click(e):
        txt_number.value = str(int(txt_number.value) + 1)
        page.update()

    page.add(
        ft.Row(
            [
                ft.IconButton(ft.icons.REMOVE, on_click=minus_click),
                txt_number,
                ft.IconButton(ft.icons.ADD, on_click=plus_click),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )


if __name__ == "__main__":
    # loop = asyncio.get_event_loop()
    # if loop.is_running():
    #     print("Can't run Flet because there's already a running event loop 😢")
    # else:
    #     loop.run_until_complete(ft.app(main))
    ret = ft.app(main)
    print("RESULT", ret)
