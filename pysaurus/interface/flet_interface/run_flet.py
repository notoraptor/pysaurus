import flet as ft

from pysaurus.interface.flet_interface.api_for_flet import ApiForFlet
from pysaurus.interface.flet_interface.page.homepage import Homepage


class App:
    def __init__(self):
        self.api = ApiForFlet()

    def run(self, page: ft.Page):
        api = self.api
        db_names = api.__run_feature__("get_database_names")

        page.title = "Pysaurus"
        page.add(ft.Container(Homepage(page, db_names), expand=True))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.api.close_app()


if __name__ == "__main__":
    with App() as app:
        ft.app(app.run)
