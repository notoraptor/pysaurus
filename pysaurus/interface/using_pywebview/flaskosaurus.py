import json
import logging
from functools import wraps

import webview
from flask import Flask, jsonify, request

from pysaurus.application import exceptions
from pysaurus.core.enumeration import EnumerationError
from pysaurus.interface.api.gui_api import GuiAPI

logger = logging.getLogger(__name__)


class _MyAPI(GuiAPI):
    __slots__ = ()


server = Flask(__name__)
server.config["SEND_FILE_MAX_AGE_DEFAULT"] = 1  # disable caching
server.api = _MyAPI()


def verify_token(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        data = json.loads(request.data)
        token = data.get("token")
        if token == webview.token:
            return function(*args, **kwargs)
        else:
            raise Exception("Authentication error")

    return wrapper


@server.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@server.route("/")
def home():
    """
    Render index.html. Initialization is performed asynchronously in initialize() function
    """
    return jsonify({"status": "ok"})


@server.route("/call/<json_command>")
@verify_token
def call(json_command):

    try:
        name, args = json.loads(json_command)
        result = {"error": False, "data": server.api.__run_feature__(name, *args)}
        return jsonify(result)
    except (OSError, EnumerationError, exceptions.PysaurusError) as exception:
        logger.exception("API call exception")
        result = {
            "error": True,
            "data": {"name": type(exception).__name__, "message": str(exception)},
        }
        return jsonify(result), 500
