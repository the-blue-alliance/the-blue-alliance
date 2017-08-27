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


class LazyDeserializer(object):
    def __init__(self):
        self._write_disabled = True  # Disable writing to DB from deserialized models for safety
        if '__id__' in self._json:
            self.key = ndb.Key(
                'Lazy{}'.format(self._json['__kind__']), self._json['__id__'])

    def __getattribute__(self, attr):
        if attr == '_json':
            return object.__getattribute__(self, attr)
        if attr in self._json:
            attr_type = self._model_type.__dict__[attr]
            return ModelSerializer.to_obj(self._json[attr], attr_type)
        return object.__getattribute__(self, attr)


class LazyAward(LazyDeserializer, Award):
    def __init__(self, json):
        self._json = json
        self._model_type = Award
        LazyDeserializer.__init__(self)
        Award.__init__(self)


class LazyDistrict(LazyDeserializer, District):
    def __init__(self, json):
        self._json = json
        self._model_type = District
        LazyDeserializer.__init__(self)
        District.__init__(self)


class LazyEvent(LazyDeserializer, Event):
    def __init__(self, json):
        self._json = json
        self._model_type = Event
        LazyDeserializer.__init__(self)
        Event.__init__(self)


class LazyEventDetails(LazyDeserializer, EventDetails):
    def __init__(self, json):
        self._json = json
        self._model_type = EventDetails
        LazyDeserializer.__init__(self)
        EventDetails.__init__(self)


class LazyLocation(LazyDeserializer, Location):
    def __init__(self, json):
        self._json = json
        self._model_type = Location
        LazyDeserializer.__init__(self)
        Location.__init__(self)


class LazyMatch(LazyDeserializer, Match):
    def __init__(self, json):
        self._json = json
        self._model_type = Match
        LazyDeserializer.__init__(self)
        Match.__init__(self)


class LazyMedia(LazyDeserializer, Media):
    def __init__(self, json):
        self._json = json
        self._model_type = Media
        LazyDeserializer.__init__(self)
        Media.__init__(self)


class LazyRobot(LazyDeserializer, Robot):
    def __init__(self, json):
        self._json = json
        self._model_type = Robot
        LazyDeserializer.__init__(self)
        Robot.__init__(self)


class LazyTeam(LazyDeserializer, Team):
    def __init__(self, json):
        self._json = json
        self._model_type = Team
        LazyDeserializer.__init__(self)
        Team.__init__(self)


class ModelSerializer(object):
    """
    Converts a model to and from a JSON serializable object.
    """
    KINDS = {
        'Award': LazyAward,
        'District': LazyDistrict,
        'Event': LazyEvent,
        'EventDetails': LazyEventDetails,
        'Location': LazyLocation,
        'Match': LazyMatch,
        'Media': LazyMedia,
        'Robot': LazyRobot,
        'Team': LazyTeam,
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
            return cls.KINDS[o['__kind__']](o)
        return o
