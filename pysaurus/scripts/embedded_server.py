from flask import url_for, send_file, Flask, request

from pysaurus.core.components import AbsolutePath


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
        <html>
            <head>
                <meta charset="utf-8">
                {code_stylesheets}
                {code_css}
                {code_javascript}
            </head>
            <body>
                {body}
                {code_scripts}
            </body>
        </html>
        """


class FlaskInterface:
    @staticmethod
    def backend_url(function, **get):
        return url_for(function.__name__, **get)

    def file(self, path):
        return send_file(AbsolutePath(path).path)

    def index(self):
        return "Hello World!"


def __wrap(method):
    def wrapper():
        if request.method == "POST":
            parameters = {**request.form}
        else:
            assert request.method == "GET", request.method
            parameters = {**request.args}
        return method(**parameters)

    wrapper.__name__ = getattr(method, "__name__")
    return wrapper


def run_flask_app(interface: FlaskInterface, debug=True, use_reloader=True):
    assert isinstance(interface, FlaskInterface)

    app = Flask(__name__)
    for name in dir(interface):
        if name.startswith("_") or name.startswith("backend_"):
            continue
        method = getattr(interface, name)
        if not callable(method):
            continue

        wrapper = __wrap(method)
        rule = "/" if name == "index" else f"/{name}"
        app.add_url_rule(rule, None, wrapper, methods=["GET", "POST"])

    return app.run(debug=debug, use_reloader=use_reloader)


def flask_gui(interface: FlaskInterface, title="", debug=True):
    import webview
    from multiprocessing import Process

    server = Process(target=run_flask_app, args=(interface, debug, False))
    server.start()

    webview.create_window(title, "http://localhost:5000")
    webview.start()
    if debug:
        print("GUI closed.")

    server.terminate()
    server.join()
    if debug:
        print("Server closed.")
