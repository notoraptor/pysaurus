import logging
from typing import List

import numpy as np

from pysaurus.core import notifications
from pysaurus.core.job_notifications import notify_job_progress, notify_job_start
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler
from pysaurus.miniature.miniature import Miniature
from saurus.language import say

logger = logging.getLogger(__name__)


def _miniature_to_x(m: Miniature) -> List:
    return list(m.r + m.g + m.b) + [1]


def _h(theta: np.ndarray, x: np.ndarray) -> float:
    return 1 / (1 + np.exp(-(theta * x).sum()))


def _cost(theta: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> float:
    return -sum(
        np.log(_h(theta, x)) if y else np.log(1 - _h(theta, x)) for x, y in zip(xs, ys)
    ) / len(xs)


def predict(m: Miniature, theta: List[float]):
    x = np.asarray(_miniature_to_x(m), dtype=np.float64)
    theta = np.asarray(theta, dtype=np.float64)
    return _h(theta, x)


def optimize_pattern_predictor(
    miniatures: List[Miniature],
    ys: List[bool],
    *,
    theta: List[float] = None,
    alpha: float = 32,
    nb_steps: int = 5000,
    database=None,
) -> List[float]:
    """Train"""
    assert len(miniatures) == len(ys) > 1
    m = len(miniatures)
    xs = np.asarray([_miniature_to_x(m) for m in miniatures], dtype=np.float64)
    ys = np.asarray(ys)
    if theta is None:
        theta = np.zeros((xs.shape[1],), dtype=np.float64)
    else:
        assert len(theta) == xs.shape[1]
        theta = np.asarray(theta, dtype=np.float64)
    logger.debug(f"xs {xs.shape} ys {ys.shape} theta {theta.shape}")
    nb_convergence = 0
    nb_expected_convergence = 10
    notifier = database.notifier if database else DEFAULT_NOTIFIER
    notify_job_start(notifier, optimize_pattern_predictor, nb_steps, "steps")
    with Profiler(say("Train"), notifier):
        with open("train.tsv", "w") as train_log:
            print("\t".join(f"t{i + 1}" for i in range(len(theta))), file=train_log)
            for step in range(nb_steps):
                # theta: (t,)
                # xs: (m, t)
                # ys: (m,)
                # 1 / (1 + np.exp(xs @ theta)) - ys -> (m,)
                # xs.T @ (1 / (1 + np.exp(xs @ theta)) - ys) -> (t, 1) -> new_theta
                if step % 100 == 0:
                    print("\t".join(str(val) for val in theta), file=train_log)
                c = _cost(theta, xs, ys)
                if nb_convergence == nb_expected_convergence:
                    notify_job_progress(
                        notifier,
                        optimize_pattern_predictor,
                        None,
                        nb_steps,
                        nb_steps,
                        title=say(
                            "Converged, # {step}, "
                            "\u00A9 {cost}, "
                            "\u03b8 [{min_theta}; {max_theta}]",
                            step=(step + 1),
                            cost=c,
                            min_theta=min(theta),
                            max_theta=max(theta),
                        ),
                    )
                    break
                previous_theta = theta
                theta = (
                    theta - alpha * (xs.T @ (1 / (1 + np.exp(-(xs @ theta))) - ys)) / m
                )
                nb_convergence = (
                    (nb_convergence + 1) if np.all(previous_theta == theta) else 0
                )
                notify_job_progress(
                    notifier,
                    optimize_pattern_predictor,
                    None,
                    step + 1,
                    nb_steps,
                    title=say(
                        "# {step}, \u00A9 {cost}, \u03b8 [{min_theta}; {max_theta}]",
                        step=(step + 1),
                        cost=c,
                        min_theta=min(theta),
                        max_theta=max(theta),
                    ),
                )
    if nb_convergence == nb_expected_convergence:
        notifier.notify(
            notifications.Message(
                say("Converged in {count} last steps.", count=nb_convergence)
            )
        )
    return list(theta)