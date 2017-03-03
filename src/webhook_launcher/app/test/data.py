import json
import os
from glob import glob

_DATA_DIR = os.path.dirname(__file__)
_DATA_JSON = {}
_DATA_OBJ = {}

for fname in glob(os.path.join(_DATA_DIR, '*.json')):
    name = os.path.splitext(os.path.split(fname)[1])[0]
    _DATA_JSON[name] = None
    _DATA_OBJ[name] = None


def get_json(name):
    if name not in _DATA_JSON:
        raise ValueError("%s data not found" % name)
    json_string = _DATA_JSON[name]
    if json_string is None:
        json_string = open(os.path.join(_DATA_DIR, '%s.json' % name)).read()
        _DATA_JSON[name] = json_string
    return json_string


def get_obj(name):
    if name not in _DATA_OBJ:
        raise ValueError("%s data not found" % name)
    obj = _DATA_OBJ[name]
    if obj is None:
        obj = json.loads(get_json(name))
        _DATA_OBJ[name] = obj
    return obj
