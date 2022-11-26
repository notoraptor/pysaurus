from pysaurus.application.application import Application


def get_database():
    app = Application()
    return app.open_database_from_name("adult videos")
