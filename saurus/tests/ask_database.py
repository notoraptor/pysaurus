import sys
from dataclasses import dataclass

from saurus.gui import frontend, theria
from saurus.sql.application import Application


@dataclass
class Collection:
    collection_id: int
    name: str
    nb_videos: int = -1
    b: int = 2

    def open(self):
        print("Hello", self.name)

    def appart(self):
        pass


def main():
    app = Application()
    collections = [
        Collection(collection_id=r[0], name=r[1])
        for r in app.db.query(
            "SELECT collection_id, name FROM collection ORDER BY name ASC"
        )
    ]
    for collection in collections:
        collection.nb_videos = app.db.query_one(
            "SELECT COUNT(video_id) FROM collection_to_video WHERE collection_id = ?",
            [collection.collection_id],
        )[0]
    rendering = theria.render(collections)
    print(rendering)
    sys.exit(frontend.gui(rendering))


if __name__ == "__main__":
    main()
