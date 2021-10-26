import sys
from typing import List

import numpy as np

from pysaurus.application.default_language import DefaultLanguage
from pysaurus.core import job_notifications
from pysaurus.core.notifier import DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler
from pysaurus.database.miniature_tools.miniature import Miniature


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


def train(
    miniatures: List[Miniature],
    ys: List[bool],
    *,
    theta: List[float] = None,
    alpha: float = 32,
    nb_steps: int = 5000,
    database=None,
) -> List[float]:
    assert len(miniatures) == len(ys) > 1
    m = len(miniatures)
    xs = np.asarray([_miniature_to_x(m) for m in miniatures], dtype=np.float64)
    ys = np.asarray(ys)
    if theta is None:
        theta = np.zeros((xs.shape[1],), dtype=np.float64)
    else:
        assert len(theta) == xs.shape[1]
        theta = np.asarray(theta, dtype=np.float64)
    print("xs", xs.shape, "ys", ys.shape, "theta", theta.shape, file=sys.stderr)
    nb_convergence = 0
    nb_expected_convergence = 10
    notifier = database.notifier if database else DEFAULT_NOTIFIER
    lang = database.lang if database else DefaultLanguage
    job_notifier = job_notifications.OptimizePatternPredictor(nb_steps, notifier)
    with Profiler(lang.profile_train, notifier):
        for step in range(nb_steps):
            # theta: (t,)
            # xs: (m, t)
            # ys: (m,)
            # 1 / (1 + np.exp(xs @ theta)) - ys -> (m,)
            # xs.T @ (1 / (1 + np.exp(xs @ theta)) - ys) -> (t, 1) -> new_theta
            c = _cost(theta, xs, ys)
            if nb_convergence == nb_expected_convergence:
                job_notifier.progress(
                    None,
                    nb_steps,
                    nb_steps,
                    title=lang.job_step_predictor_opt_converged.format(
                        cost=c, min_theta=min(theta), max_theta=max(theta)
                    ),
                )
                break
            previous_theta = theta
            theta = theta - alpha * (xs.T @ (1 / (1 + np.exp(-(xs @ theta))) - ys)) / m
            nb_convergence = (
                (nb_convergence + 1) if np.all(previous_theta == theta) else 0
            )
            job_notifier.progress(
                None,
                step + 1,
                nb_steps,
                title=lang.job_step_predictor_opt.format(
                    step=(step + 1), cost=c, min_theta=min(theta), max_theta=max(theta)
                ),
            )
    if nb_convergence == nb_expected_convergence:
        notifier.notify(
            lang.message_predictor_opt_converged.format(count=nb_convergence)
        )
    return list(theta)
