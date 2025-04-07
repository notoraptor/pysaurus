import logging

from pysaurus.core.informer import Informer
from pysaurus.interface.using_pywebview.webview_server import WebviewServer


def main():
    with Informer.default():
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # Create and start the server
        server = WebviewServer(port=8000)
        try:
            server.start()
        except KeyboardInterrupt:
            logging.info("Shutting down...")
        finally:
            server.stop()


if __name__ == "__main__":
    main()
