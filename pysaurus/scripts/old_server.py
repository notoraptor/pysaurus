from flask import Flask, url_for, request, send_file
from pysaurus.core.components import AbsolutePath
import os

size = 1000
APP = Flask(__name__)
APP.debug = True


@APP.route("/")
def index():
    path = AbsolutePath.join(os.path.dirname(__file__), "miwa.jpg")
    fields = "".join(
        f'<div><input type="radio" name="input{i}" value="{i}-0"/><input type="radio" name="input{i}" value="{i}-1" checked/></div>'
        for i in range(size)
    )
    return f"""
    <p><a href="{url_for('image', path=path.path)}">Image</a></p>
    <form method="post" action="{url_for('test')}">
    <div><input type="submit" value="send"/></div>
    {fields}
    </form>
    """
    # return f'Hello! <a href="{url_for("test")}">Click here!</a'


@APP.route("/test", methods=["POST"])
def test():
    assert len(request.form) == size, (len(request.form), size)
    for k in request.form.keys():
        print("Got", k, request.form[k])
    return f'<a href="{url_for("index")}">Back ({len(request.form)})!</a>'


@APP.route("/image")
def image():
    path = AbsolutePath(request.args["path"])
    return send_file(path.path)


APP.run()
