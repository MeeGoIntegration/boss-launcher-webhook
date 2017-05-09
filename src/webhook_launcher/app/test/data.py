# Copyright (C) 2017 Jolla Ltd.
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to
# the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

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
