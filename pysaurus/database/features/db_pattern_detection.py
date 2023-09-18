from typing import Dict, List

from pysaurus.application.exceptions import PysaurusError
from pysaurus.core.job_notifications import notify_job_progress, notify_job_start
from pysaurus.core.modules import ImageUtils
from pysaurus.core.notifications import Message
from pysaurus.core.profiling import Profiler
from pysaurus.database.database import Database
from pysaurus.database.features.machine_learning import (
    optimize_pattern_predictor,
    predict,
)
from saurus.language import say


class NoVideoForClass0(PysaurusError):
    pass


class NoVideoForClass1(PysaurusError):
    pass


class NoPredictor(PysaurusError):
    pass


class DbPatternDetection:
    @staticmethod
    def create_prediction_property(database: Database, prop_name: str):
        database.create_prop_type(f"<?{prop_name}>", int, [-1, 0, 1], False)

    @classmethod
    def compute_pattern_detector(cls, database: Database, prop_name: str):
        assert cls._is_prediction_property(database, prop_name)
        video_id_to_miniature = {
            m.video_id: m for m in database.ensure_miniatures(returns=True)
        }
        video_indices = [
            video["video_id"]
            for video in database.select_videos_fields(
                ["video_id"], "readable", "with_thumbnails"
            )
            if video["video_id"] in video_id_to_miniature
        ]
        classifier: Dict[int, List[int]] = {}
        for video_id in video_indices:
            (prop_val,) = database.get_prop_values(video_id, prop_name) or [-1]
            classifier.setdefault(prop_val, []).append(video_id)
        if 0 not in classifier:
            raise NoVideoForClass0(prop_name)
        if 1 not in classifier:
            raise NoVideoForClass1(prop_name)
        database.notifier.notify(
            Message(
                say(
                    "Training set: false {count0}, true {count1}",
                    count0=len(classifier[0]),
                    count1=len(classifier[1]),
                )
            )
        )
        video_id_to_class = {video_id: False for video_id in classifier[0]}
        video_id_to_class.update({video_id: True for video_id in classifier[1]})
        miniatures = []
        classes = []
        for video_id, y in video_id_to_class.items():
            miniatures.append(video_id_to_miniature[video_id])
            classes.append(video_id_to_class[video_id])
        theta = optimize_pattern_predictor(
            miniatures,
            classes,
            theta=database.get_predictor(prop_name),
            database=database,
        )
        database.set_predictor(prop_name, theta)

    @classmethod
    def predict_pattern(cls, database: Database, prop_name: str):
        """Apply pattern detector."""
        theta = database.get_predictor(prop_name)
        if not theta:
            raise NoPredictor(prop_name)
        video_id_to_miniature = {
            m.video_id: m for m in database.ensure_miniatures(returns=True)
        }
        video_indices = [
            video["video_id"]
            for video in database.select_videos_fields(
                ["video_id"], "readable", "with_thumbnails"
            )
            if video["video_id"] in video_id_to_miniature
        ]
        output_prop_name = "<!" + prop_name[2:]
        with database.to_save():
            if not database.has_prop_type(output_prop_name):
                database.create_prop_type(output_prop_name, int, [0, 1], False)
            notify_job_start(
                database.notifier, cls.predict_pattern, len(video_indices), "videos"
            )
            with Profiler(say("Predict"), database.notifier):
                for i, video_id in enumerate(video_indices):
                    database.set_prop_values(
                        video_id,
                        output_prop_name,
                        [int(predict(video_id_to_miniature[video_id], theta) >= 0.5)],
                    )
                    notify_job_progress(
                        database.notifier,
                        cls.predict_pattern,
                        None,
                        i + 1,
                        len(video_indices),
                    )

        return output_prop_name

    @staticmethod
    def _is_prediction_property(db: Database, name: str) -> bool:
        return (
            name.startswith("<?")
            and name.endswith(">")
            and db.has_prop_type(name, multiple=False, with_enum=[-1, 0, 1])
        )

    @staticmethod  # Unused
    def _generate_pattern_heatmap(theta: List[float]):
        w, h = ImageUtils.THUMBNAIL_SIZE
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
            pixel_thetas[i] = int(
                255 * (pixel_thetas[i] - min_val) / (max_val - min_val)
            )
        rs = pixel_thetas[:size]
        gs = pixel_thetas[size : 2 * size]
        bs = pixel_thetas[2 * size :]
        assert len(rs) == len(gs) == len(bs) == size
        list(zip(rs, gs, bs))
