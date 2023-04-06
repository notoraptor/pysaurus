"""Currently unused."""

import atexit

from pysaurus.application.application import Application


class ClosingApplication(Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        atexit.register(self._close)

    def _close(self):
        print(f"Closing {self.app_name}, saving databases.")
        for path, database in self.databases.items():
            if database:
                with database.to_save():
                    print("Saving", path.file_title)
        print(f"Closed {self.app_name}.")
