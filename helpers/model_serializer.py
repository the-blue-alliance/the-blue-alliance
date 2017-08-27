import datetime
from google.appengine.ext import ndb

from models.award import Award
from models.district import District
from models.event import Event
from models.event_details import EventDetails
from models.location import Location
from models.match import Match
from models.media import Media
from models.robot import Robot
from models.team import Team


class ModelSerializer(object):
    """
    Converts a model to and from a JSON serializable object.
    """
    KINDS = {
        'Award': Award,
        'District': District,
        'Event': Event,
        'EventDetails': EventDetails,
        'Location': Location,
        'Match': Match,
        'Media': Media,
        'Robot': Robot,
        'Team': Team,
    }

    @classmethod
    def to_json(cls, o):
        if isinstance(o, list):
            return [cls.to_json(l) for l in o]
        if isinstance(o, dict):
            x = {}
            for l in o:
                x[l] = cls.to_json(o[l])
            return x
        if isinstance(o, datetime.datetime):
            return o.strftime('%Y-%m-%dT%H:%M:%S.%f')
        if isinstance(o, ndb.GeoPt):
            return {'lat': o.lat, 'lon': o.lon}
        if isinstance(o, ndb.Key):
            return {'__kind__': o.kind(), 'id': o.id()}
        if isinstance(o, ndb.Model):
            dct = {
                '__kind__': type(o).__name__,
            }
            if o.key:
                dct['__id__'] = o.key.id()
            for attr_name in o.to_dict():
                if hasattr(o, attr_name):
                    dct[attr_name] = cls.to_json(getattr(o, attr_name))
            return dct
        return o

    @classmethod
    def to_obj(cls, o, obj_type=None):
        if o is None:
            return None
        if isinstance(o, list):
            return [cls.to_obj(l, obj_type) for l in o]
        if isinstance(obj_type, ndb.DateTimeProperty):
            return datetime.datetime.strptime(o, '%Y-%m-%dT%H:%M:%S.%f')
        if isinstance(obj_type, ndb.GeoPtProperty):
            return ndb.GeoPt(o['lat'], o['lon'])
        if isinstance(obj_type, ndb.KeyProperty):
            return ndb.Key(o['__kind__'], o['id'])
        if obj_type is None or isinstance(obj_type, ndb.StructuredProperty):
            obj_type = cls.KINDS[o['__kind__']]
            if obj_type is not None:
                obj = obj_type(id=o.get('__id__'))
                obj._write_disabled = True  # Disable writing to DB from deserialized models for safety
                for attr_name in obj.to_dict():
                    attr_type = obj_type.__dict__[attr_name]
                    setattr(
                        obj,
                        attr_name,
                        cls.to_obj(o.get(attr_name), attr_type)
                    )
                return obj
        return o
