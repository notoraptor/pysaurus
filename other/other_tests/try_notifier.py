import queue
import threading
import time

from pysaurus.core.informer import Informer
from pysaurus.core.profiling import Profiler
from pysaurus.interface.api.api_utils.console_notification_printer import (
    ConsoleNotificationPrinter,
)


def _monitor_notifications(notifier: Informer) -> None:
    # We are in a thread, with notifications handled sequentially,
    # thus no need to be process-safe.
    print("Monitoring notifications ...")
    main_thread = threading.main_thread()
    notification_printer = ConsoleNotificationPrinter()
    counter = 0
    while True:
        if counter >= 100 and not main_thread.is_alive():
            print("Main thread terminated, exiting notifications monitor.")
            break
        try:
            notification = notifier.next_or_crash()
            notification_printer.print(notification)
            counter = 0
        except queue.Empty:
            time.sleep(1 / 100)
            counter += 1
    print("End monitoring.")


def main():
    with Informer.default():
        with Profiler("Test"):
            x = 1 + 2


if __name__ == "__main__":
    main()
