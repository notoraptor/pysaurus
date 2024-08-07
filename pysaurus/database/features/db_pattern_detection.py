from typing import Dict, List

from pysaurus.application.exceptions import PysaurusError
from pysaurus.core.informer import Informer
from pysaurus.core.modules import ImageUtils
from pysaurus.core.notifications import Message
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase
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
    def create_prediction_property(database: AbstractDatabase, prop_name: str):
        database.create_prop_type(f"<?{prop_name}>", int, [-1, 0, 1], False)

    @classmethod
    def compute_pattern_detector(cls, database: AbstractDatabase, prop_name: str):
        assert cls._is_prediction_property(database, prop_name)
        notifier = Informer.default()
        video_id_to_miniature = {m.video_id: m for m in database.ensure_miniatures()}
        video_indices = [
            video["video_id"]
            for video in database.select_videos_fields(
                ["video_id"], "readable", "with_thumbnails"
            )
            if video["video_id"] in video_id_to_miniature
        ]
        classifier: Dict[int, List[int]] = {}
        prop_vals = database.get_all_prop_values(prop_name, video_indices)
        for video_id in video_indices:
            (prop_val,) = prop_vals.get(video_id, [-1])
            classifier.setdefault(prop_val, []).append(video_id)
        if 0 not in classifier:
            raise NoVideoForClass0(prop_name)
        if 1 not in classifier:
            raise NoVideoForClass1(prop_name)
        notifier.notify(
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
            notifier=Informer.default(),
        )
        database.set_predictor(prop_name, theta)

    @classmethod
    def predict_pattern(cls, database: AbstractDatabase, prop_name: str):
        """Apply pattern detector."""
        notifier = Informer.default()
        theta = database.get_predictor(prop_name)
        if not theta:
            raise NoPredictor(prop_name)
        video_id_to_miniature = {m.video_id: m for m in database.ensure_miniatures()}
        video_indices = [
            video["video_id"]
            for video in database.select_videos_fields(
                ["video_id"], "readable", "with_thumbnails"
            )
            if video["video_id"] in video_id_to_miniature
        ]
        output_prop_name = "<!" + prop_name[2:]
        with database.to_save():
            if not database.get_prop_types(name=output_prop_name):
                database.create_prop_type(output_prop_name, int, [0, 1], False)
            notifier.task(cls.predict_pattern, len(video_indices), "videos")
            with Profiler(say("Predict")):
                for i, video_id in enumerate(video_indices):
                    database.set_video_prop_values(
                        output_prop_name,
                        {
                            video_id: [
                                int(
                                    predict(video_id_to_miniature[video_id], theta)
                                    >= 0.5
                                )
                            ]
                        },
                    )
                    notifier.progress(cls.predict_pattern, i + 1, len(video_indices))

        return output_prop_name

    @staticmethod
    def _is_prediction_property(db: AbstractDatabase, name: str) -> bool:
        return (
            name.startswith("<?")
            and name.endswith(">")
            and db.get_prop_types(name=name, multiple=False, with_enum=[-1, 0, 1])
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
