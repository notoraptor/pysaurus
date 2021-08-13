"""
Requirements:
Flask==2.0.1
pywebview==3.5
"""

from multiprocessing import Process

import webview
from flask import Flask, request, send_file, url_for

from pysaurus.core.components import AbsolutePath


def __function_to_flask(method):
    def wrapper():
        if request.method == "POST":
            parameters = {**request.form}
        else:
            assert request.method == "GET", request.method
            parameters = {**request.args}
        return method(**parameters)

    wrapper.__name__ = getattr(method, "__name__")
    return wrapper


class HTML:
    def __init__(self, *, stylesheets=(), scripts=(), css="", javascript=""):
        self.stylesheets = stylesheets
        self.scripts = scripts
        self.css = css
        self.javascript = javascript

    def __call__(self, body):
        code_stylesheets = "".join(
            f'<link rel="stylesheet" href="{stylesheet}"/>'
            for stylesheet in self.stylesheets
        )

        code_scripts = "".join(
            f'<script src="{script}"></script>' for script in self.scripts
        )

        code_css = f'<style type="text/css">{self.css}</style>' if self.css else ""

        code_javascript = (
            f'<script type="text/javascript">{self.javascript}</script>'
            if self.javascript
            else ""
        )

        return f"""
         <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8">
                {code_stylesheets}
                {code_css}
            </head>
            <body>
                {body}
                {code_scripts}
                {code_javascript}
            </body>
        </html>
        """


class FlaskInterface:
    @staticmethod
    def backend_url(function, **get):
        """Generate a url to given function with givne parameters."""
        return url_for(function.__name__, **get)

    def file(self, path):
        """Utility page to download a file."""
        return send_file(AbsolutePath(path).path)

    def index(self):
        """Default home page function."""
        return "Hello World!"


def flask_server(interface: FlaskInterface, debug=True, use_reloader=True, port=None):
    assert isinstance(interface, FlaskInterface)

    app = Flask(__name__)
    for name in dir(interface):
        if name.startswith("_") or name.startswith("backend_"):
            continue
        method = getattr(interface, name)
        if not callable(method):
            continue

        wrapper = __function_to_flask(method)
        rule = "/" if name == "index" else f"/{name}"
        app.add_url_rule(rule, None, wrapper, methods=["GET", "POST"])

    return app.run(debug=debug, use_reloader=use_reloader, port=port)


def flask_gui(interface: FlaskInterface, title="", debug=True, port=None):
    server = Process(target=flask_server, args=(interface, debug, False, port))
    server.start()

    webview.create_window(title, "http://localhost:5000")
    webview.start()
    if debug:
        print("GUI closed.")

    server.terminate()
    server.join()
    if debug:
        print("Server closed.")
