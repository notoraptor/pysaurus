"""Entry point for the videre (videroid) interface.

Run with:  uv run -m pysaurus.interface.videroid.run_with_videroid
"""

import sys

from pysaurus.core.informer import Information
from pysaurus.interface.videroid.app import VideroidApp


def main() -> None:
    # GuiAPI (created inside VideroidApp) subscribes to Information and starts
    # the video server, so the whole app must live inside the Information context.
    with Information():
        app = VideroidApp()
        sys.exit(app.run())


if __name__ == "__main__":  # pragma: no cover
    main()
