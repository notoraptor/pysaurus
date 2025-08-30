import os
import threading

import webview
from flask import Flask, send_from_directory

from pysaurus.core.informer import Informer
from pysaurus.interface.using_pywebview.webview_server import Backend

# Définir le répertoire à servir
DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "web")
assert os.path.isdir(DIRECTORY)

# Créer une application Flask
app = Flask(__name__)


@app.route("/<path:filename>")
def serve_file(filename):
    return send_from_directory(DIRECTORY, filename)


@app.route("/")
def index():
    return send_from_directory(DIRECTORY, "index.html")


# Fonction pour démarrer le serveur Flask
def start_flask_server():
    app.run(port=5000)


def inject_console_interceptor(window):
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
    window.evaluate_js(js_code)


def main():
    with Informer.default():
        server_thread = threading.Thread(target=start_flask_server, daemon=True)
        server_thread.start()

        backend = Backend()
        window = webview.create_window(
            "Local Files",
            "http://localhost:5000",
            width=1500,
            height=1000,
            resizable=True,
            min_size=(800, 600),
            js_api=backend,
        )
        backend.__window__ = window

        def injector():
            inject_console_interceptor(window)

        window.events.loaded += injector
        webview.start()


if __name__ == "__main__":
    main()
