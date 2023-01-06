from typing import List

from pysaurus.application.application import Application
from pysaurus.database.machine_learning import optimize_pattern_predictor, predict
from pysaurus.database.miniature_tools.miniature import Miniature
from pysaurus.database.video import Video


def main():
    app = Application()
    db = app.open_database_from_name("adult videos")
    all_miniatures = db.ensure_miniatures(returns=True)  # type: List[Miniature]
    video_id_to_miniature = {m.video_id: m for m in all_miniatures}
    videos = db.get_videos("readable", "with_thumbnails")  # type: List[Video]
    prop_name = "<?newsensations>"
    classifier = {}
    for video in videos:
        prop_val = video.properties.get(prop_name, -1)
        classifier.setdefault(prop_val, []).append(video)
    assert 0 in classifier
    assert 1 in classifier
    negative_videos = classifier[0]
    positive_videos = classifier[1]
    video_id_to_class = {video.video_id: False for video in negative_videos}
    video_id_to_class.update({video.video_id: True for video in positive_videos})
    miniatures = []
    classes = []
    for video_id, y in video_id_to_class.items():
        miniatures.append(video_id_to_miniature[video_id])
        classes.append(video_id_to_class[video_id])
    theta = optimize_pattern_predictor(miniatures, classes)
    print("Predictions:")
    for i, (x, y) in enumerate(zip(miniatures, classes)):
        p = predict(x, theta)
        b = p >= 0.5 if y else p < 0.5
        print("Image", i + 1, "expects", y, "predicts", p, "good?", b)


if __name__ == "__main__":
    main()
