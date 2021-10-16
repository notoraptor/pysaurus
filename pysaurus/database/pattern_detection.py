from typing import List

from pysaurus.application.exceptions import PysaurusError
from pysaurus.core import job_notifications
from pysaurus.core.modules import ImageUtils
from pysaurus.core.notifications import Message
from pysaurus.core.profiling import Profiler
from pysaurus.database.database import Database
from pysaurus.database.machine_learning import predict, train
from pysaurus.database.properties import PropType
from pysaurus.database.video import Video


def _is_prediction_property(prop: PropType):
    return (
        prop.name.startswith("<?")
        and prop.name.endswith(">")
        and prop.definition == [-1, 0, 1]
        and not prop.multiple
    )


def compute_pattern_detector(db: Database, videos: List[Video], prop_name: str):
    assert _is_prediction_property(db.get_prop_type(prop_name))
    video_id_to_miniature = {m.video_id: m for m in db.ensure_miniatures(returns=True)}
    videos = [v for v in videos if v.video_id in video_id_to_miniature]
    classifier = {}
    for video in videos:
        prop_val = video.properties.get(prop_name, -1)
        classifier.setdefault(prop_val, []).append(video)
    if 0 not in classifier:
        raise PysaurusError(f"No video tagged with 0 for {prop_name}")
    if 1 not in classifier:
        raise PysaurusError(f"No video tagged with 1 for {prop_name}")
    db.notifier.notify(
        Message(f"Training set: false {len(classifier[0])}, true {len(classifier[1])}")
    )
    video_id_to_class = {video.video_id: False for video in classifier[0]}
    video_id_to_class.update({video.video_id: True for video in classifier[1]})
    miniatures = []
    classes = []
    for video_id, y in video_id_to_class.items():
        miniatures.append(video_id_to_miniature[video_id])
        classes.append(video_id_to_class[video_id])
    theta = train(miniatures, classes, theta=db.get_predictor(prop_name), database=db)
    db.set_predictor(prop_name, theta)
    db.save()


def apply_pattern_detector(db: Database, videos: List[Video], prop_name: str):
    theta = db.get_predictor(prop_name)
    if not theta:
        raise PysaurusError(f"No predictor for {prop_name}")
    video_id_to_miniature = {m.video_id: m for m in db.ensure_miniatures(returns=True)}
    videos = [v for v in videos if v.video_id in video_id_to_miniature]
    output_prop_name = "<!" + prop_name[2:]
    if not db.has_prop_type(output_prop_name):
        db.add_prop_type(PropType(output_prop_name, [0, 1]), save=False)
    job_notifier = job_notifications.PredictPattern(len(videos), db.notifier)
    with Profiler(db.lang.profile_predict, db.notifier):
        for i, video in enumerate(videos):
            video.properties[output_prop_name] = int(
                predict(video_id_to_miniature[video.video_id], theta) >= 0.5
            )
            job_notifier.progress(None, i + 1, len(videos))

    db.notifier.notify(Message(f"Predicted {len(videos)} videos"))
    db.save()
    return output_prop_name


def generate_pattern_heatmap(theta: List[float]):
    w, h = ImageUtils.DEFAULT_THUMBNAIL_SIZE
    size = w * h
    assert len(theta) == 3 * size + 1
    pixel_thetas = theta[:-1]
    supplementary = theta[-1]
    assert len(pixel_thetas) == 3 * size
    supp_piece = supplementary / (3 * size)
    for i in range(len(pixel_thetas)):
        pixel_thetas[i] += supp_piece
    min_val = min(pixel_thetas)
    max_val = max(pixel_thetas)
    for i in range(len(pixel_thetas)):
        pixel_thetas[i] = int(255 * (pixel_thetas[i] - min_val) / (max_val - min_val))
    rs = pixel_thetas[:size]
    gs = pixel_thetas[size : 2 * size]
    bs = pixel_thetas[2 * size :]
    assert len(rs) == len(gs) == len(bs) == size
    output = list(zip(rs, gs, bs))
