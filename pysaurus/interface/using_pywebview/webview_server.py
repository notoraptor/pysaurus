import http.server
import json
import logging
import os
import socketserver
import threading

import webview

from pysaurus.application import exceptions
from pysaurus.core.enumeration import EnumerationError
from pysaurus.core.notifications import Notification
from pysaurus.interface.api.gui_api import GuiAPI

logger = logging.getLogger(__name__)


class MyAPI(GuiAPI):
    __slots__ = ("window",)

    def __init__(self):
        super().__init__()
        self.window = None

    def _notify(self, notification: Notification) -> None:
        nt = notification.describe()
        self.window.evaluate_js(f"window.NOTIFICATION_MANAGER.call({json.dumps(nt)})")


class Backend:
    __api__ = None
    __window__ = None

    def api(self):
        if self.__api__ is None:
            self.__api__ = MyAPI()
        if self.__window__:
            self.__api__.window = self.__window__
        return self.__api__

    def call(self, call_args):
        api = self.api()
        try:
            name, args = call_args
            result = {"error": False, "data": api.__run_feature__(name, *args)}
        except (OSError, EnumerationError, exceptions.PysaurusError) as exception:
            logger.exception("API call exception")
            result = {
                "error": True,
                "data": {"name": type(exception).__name__, "message": str(exception)},
            }
        return result

    @classmethod
    def handle_js_log(cls, message):
        """Handle JavaScript console.log messages"""
        try:
            # Try to parse as JSON if it's a string
            if isinstance(message, str):
                try:
                    message = json.loads(message)
                except json.JSONDecodeError:
                    pass

            # Format the message
            if isinstance(message, (dict, list)):
                message = json.dumps(message, indent=2)

            print(f"JS Log: {message}")
        except Exception as e:
            print(f"Error handling JS log: {e}")


class WebviewServer:
    def __init__(self, port=8000):
        self.port = port
        self.server = None
        self.thread = None
        self.window = None
        self.backend = Backend()

    def start_server(self):
        """Start the HTTP server in a separate thread"""
        # Get the absolute path to the build directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        build_dir = os.path.join(current_dir, "..", "web")
        assert os.path.isdir(build_dir), f"Build directory not found: {build_dir}"

        # Change to the build directory to serve files from there
        os.chdir(build_dir)

        # Create and start the server
        handler = http.server.SimpleHTTPRequestHandler
        self.server = socketserver.TCPServer(("", self.port), handler)
        logger.info(f"Serving web interface at http://localhost:{self.port}")
        self.server.serve_forever()

    def start(self):
        """Start both the server and the webview window"""
        # Start the server in a separate thread
        self.thread = threading.Thread(target=self.start_server, daemon=True)
        self.thread.start()

        # Create and start the webview window
        self.window = webview.create_window(
            "Pysaurus",
            f"http://localhost:{self.port}/index.html",
            width=1500,
            height=900,
            resizable=True,
            min_size=(800, 600),
            js_api=self.backend,
        )
        self.backend.__window__ = self.window

        # Inject the console.log interceptor
        self.window.events.loaded += self.inject_console_interceptor

        # Start the webview
        webview.start()

    def inject_console_interceptor(self):
        """Inject JavaScript code to intercept console.log"""
        js_code = """
        (function() {
            const originalConsole = {
                log: console.log,
                warn: console.warn,
                error: console.error,
                info: console.info,
                debug: console.debug
            };

            function interceptConsole(type) {
                console[type] = function(...args) {
                    // Call original console method
                    originalConsole[type].apply(console, args);

                    // Send to Python
                    try {
                        pywebview.api.handle_js_log(args.length === 1 ? args[0] : args);
                    } catch (e) {
                        originalConsole.error('Failed to send log to Python:', e);
                    }
                };
            }

            ['log', 'warn', 'error', 'info', 'debug'].forEach(interceptConsole);
            console.info('injected');
            
            window.backend_call = function (name, args) {
                return new Promise((resolve, reject) => {
                    pywebview.api
                        .call([name, args])
                        .then((result) => {
                            if (result.error) {
                                reject(result.data);
                            } else {
                                resolve(result.data);
                            }
                        })
                        .catch((error) => reject({ name: "javascript error", message: error.message }));
                });
            };
            console.log('import');
            System.import("./build/index.js");
            console.log('imported');
        })();
        """
        self.window.evaluate_js(js_code)

    def stop(self):
        """Stop both the server and the webview window"""
        if self.backend:
            api = self.backend.api()
            if api:
                api.close_app()
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.window:
            self.window.destroy()
