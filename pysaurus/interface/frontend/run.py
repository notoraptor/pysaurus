import os

import ujson as json
from flask import Flask, send_file, Response

from pysaurus.application.application import Application
from pysaurus.core.components import AbsolutePath
from pysaurus.core.functions import package_dir
from pysaurus.database.viewport.layers.source_layer import SourceLayer

entry_path = AbsolutePath.join(
    package_dir(), "interface", "cefgui", "web", "index.html"
)
relative_path = os.path.relpath(entry_path.path)


# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_folder=entry_path.get_directory().path)


@app.route('/')
def index():
    return send_file(entry_path.path)


@app.route("/backend.js")
def js_backend():
    ret = f"""
window.PYTHON_DEFAULT_SOURCES = {json.dumps(SourceLayer.DEFAULT_SOURCE_DEF)};
window.PYTHON_APP_NAME = {json.dumps(Application.app_name)};
System.import('./build/client.js');
"""
    return Response(ret, mimetype="text/javascript")


@app.route("/onload.js")
def js_index():
    ret = f"""console.log("onload.");"""
    return Response(ret, mimetype="text/javascript")


@app.route("/<path:path>")
def serve(path):
    file_path = AbsolutePath.join(entry_path.get_directory(), path)
    assert file_path.isfile(), file_path
    return send_file(file_path.path)


if __name__ == "__main__":
    app.run(port=2000)
