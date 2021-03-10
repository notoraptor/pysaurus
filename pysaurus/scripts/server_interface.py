from flask import url_for, send_file, Flask, request

from pysaurus.core.components import AbsolutePath


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


def flask_gui(interface: FlaskInterface, title='', debug=True):
    import webview
    from multiprocessing import Process

    server = Process(target=run_flask_app, args=(interface, debug, False))
    server.start()

    webview.create_window(title, "http://localhost:5000")
    webview.start()
    if debug:
        print('GUI closed.')

    server.terminate()
    server.join()
    if debug:
        print('Server closed.')
