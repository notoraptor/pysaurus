import inspect
from typing import Dict, List

from pysaurus.core.job_notifications import JobStep, JobToDo
from pysaurus.core.notifications import Notification
from pysaurus.interface.flet_interface.page.taskpage import ProgressionMonitoring


class NotificationCollector:
    __slots__ = ("notifications", "job_map")

    def __init__(self):
        self.notifications: List[Notification] = []
        self.job_map: Dict[str, ProgressionMonitoring] = {}

    def on_job_to_do(self, notification: JobToDo):
        assert notification.name not in self.job_map, (
            notification,
            self.job_map.keys(),
        )
        self.job_map[notification.name] = ProgressionMonitoring(notification)
        self.notifications.append(notification)

    def on_job_step(self, notification: JobStep):
        assert notification.name in self.job_map, (
            notification,
            self.job_map.keys(),
        )
        monitoring = self.job_map[notification.name]
        monitoring.collect(notification)
        # We collect JobStep in monitoring object, not in notifications list.

    def on(self, notification: Notification):
        self.notifications.append(notification)


class Overridden:
    def __init__(self, polymorph, basename="on"):
        assert not inspect.isclass(polymorph)
        prefix = f"{basename}_"
        self.methods = {}
        self.base_method = None
        for name, method in inspect.getmembers(polymorph, inspect.ismethod):
            if name == basename or name.startswith(prefix):
                signature = inspect.signature(method)
                annotations = []
                for param in signature.parameters.values():
                    # NB: It seems, if method comes from an instance, then
                    # signature won't contain first `self` parameter.

                    # NB: We don't want *args and **kwargs.
                    assert param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD)

                    assert param.annotation
                    annotations.append(param.annotation)
                self.methods[tuple(annotations)] = method
                if name == basename:
                    self.base_method = method

    def __call__(self, *args):
        pass
