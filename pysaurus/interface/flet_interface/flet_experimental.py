from pysaurus.core import notifications
from pysaurus.core.job_notifications import JobStep, JobToDo
from pysaurus.core.overridden import Overridden
from pysaurus.interface.flet_interface.page.taskpage_utils import NotificationCollector

ov = Overridden(NotificationCollector())

ov(JobToDo("name", 200))
ov(JobStep("name", "channel", 0, 100))
ov(notifications.Notification())
ov(notifications.Message("message"))
ov(12)
