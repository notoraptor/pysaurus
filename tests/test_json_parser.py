import pytest
import ujson as json

from pysaurus.core.custom_json_parser import json_parse_string


def run(data):
    if isinstance(data, str):
        json_parse_string(data)
    else:
        jsn = json.dumps(data)
        prs = json_parse_string(jsn)
        assert data == prs


def fail(data, exc_type=Exception, exc_match=None):
    with pytest.raises(exc_type, match=exc_match):
        run(data)


def test_simple_arr():
    run([1, 2.5, True, False, "a string", None])


def test_simple_dict():
    run({"a": 1, "b": 2.5, "c": True, "d": False, "e": "a string", "f": None})


def test_error_list():
    fail("[2,]", ValueError, "final comma count")
