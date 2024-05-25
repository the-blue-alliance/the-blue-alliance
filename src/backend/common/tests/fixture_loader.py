# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License

"""
Ported from https://github.com/rbanffy/appengine-fixture-loader
Updated to use Google Cloud NDB + Python3
"""

import json
from datetime import date, datetime, time

from google.appengine.ext import ndb
from google.appengine.ext.ndb.model import (
    DateProperty,
    DateTimeProperty,
    KeyProperty,
    TimeProperty,
)


def _sensible_value(attribute_type, value):
    if type(attribute_type) is DateTimeProperty:
        retval = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
    elif type(attribute_type) is TimeProperty:
        try:
            dt = datetime.strptime(value, "%H:%M:%S")
        except ValueError:
            dt = datetime.strptime(value, "%H:%M")
        retval = time(dt.hour, dt.minute, dt.second)
    elif type(attribute_type) is DateProperty:
        dt = datetime.strptime(value, "%Y-%m-%d")
        retval = date(dt.year, dt.month, dt.day)
    elif type(attribute_type) is KeyProperty and value is not None:
        retval = ndb.Key(attribute_type._kind, value)
    else:
        retval = value

    return retval


def load_fixture(filename, kind, post_processor=None):
    """
    Loads a file into entities of a given class, run the post_processor on each
    instance before it's saved
    """

    def _load(od, kind, post_processor, parent=None, presets={}):
        """
        Loads a single dictionary (od) into an object, overlays the values in
        presets, persists it and
        calls itself on the objects in __children__* keys
        """
        if hasattr(kind, "keys"):  # kind is a map
            objtype = kind[od["__kind__"]]
        else:
            objtype = kind

        obj_id = od.get("__id__")
        if obj_id is not None:
            obj = objtype(id=obj_id, parent=parent)
        else:
            obj = objtype(parent=parent)
        obj._fix_up_properties()

        # Iterate over the non-special attributes and overlay the presets
        for attribute_name in [
            k for k in od.keys() if not k.startswith("__") and not k.endswith("__")
        ] + list(presets.keys()):
            if attribute_name not in obj._properties:
                continue
            attribute_type = obj._properties[attribute_name]
            attribute_value = _sensible_value(
                attribute_type, presets.get(attribute_name, od.get(attribute_name))
            )
            attribute_type._set_value(obj, attribute_value)

        if post_processor:
            post_processor(obj)

        # Saving obj is required to continue with the children
        obj.put()

        loaded = [obj]

        # Process ancestor-based __children__
        for item in od.get("__children__", []):
            loaded.extend(_load(item, kind, post_processor, parent=obj.key))

        # Process other __children__[key]__ items
        for child_attribute_name in [
            k for k in od.keys() if k.startswith("__children__") and k != "__children__"
        ]:
            attribute_name = child_attribute_name.split("__")[-2]

            for child in od[child_attribute_name]:
                loaded.extend(
                    _load(
                        child, kind, post_processor, presets={attribute_name: obj.key}
                    )
                )

        return loaded

    with open(filename) as f:
        tree = json.load(f)

    loaded = []

    # Start with the top-level of the tree
    for item in tree:
        loaded.extend(_load(item, kind, post_processor))

    return loaded
