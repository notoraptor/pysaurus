from pysaurus.application.application import Application


def main():
    app = Application()
    db = app.open_database_from_name("adult videos")
    cl = db.select(
        "video",
        [":actress"],
        'readable and "actress" in properties and len(properties["actress"]) > 1',
    )
    print(len(cl))


if __name__ == "__main__":
    main()
