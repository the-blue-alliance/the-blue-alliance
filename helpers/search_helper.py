from google.appengine.api import search


class SearchHelper(object):
    EVENT_LOCATION_INDEX = 'eventLocation'
    TEAM_LOCATION_INDEX = 'teamLocation'

    @classmethod
    def add_event_location_index(cls, event):
        if event.normalized_location and event.normalized_location.lat_lng:
            fields = [
                search.NumberField(name='year', value=event.year),
                search.GeoField(name='location', value=search.GeoPoint(
                    event.normalized_location.lat_lng.lat,
                    event.normalized_location.lat_lng.lon))
            ]
            search.Index(name="eventLocation").put(
                search.Document(doc_id=event.key.id(), fields=fields))

    @classmethod
    def remove_event_location_index(cls, event):
        search.Index(name=EVENT_LOCATION_INDEX).delete(event.key.id())

    @classmethod
    def add_team_location_index(cls, team):
        if team.normalized_location and team.normalized_location.lat_lng:
            fields = [
                search.GeoField(name='location', value=search.GeoPoint(
                    team.normalized_location.lat_lng.lat,
                    team.normalized_location.lat_lng.lon))
            ]
            search.Index(name=cls.TEAM_LOCATION_INDEX).put(
                search.Document(doc_id=team.key.id(), fields=fields))

    @classmethod
    def remove_team_location_index(cls, team):
        search.Index(name=TEAM_LOCATION_INDEX).delete(team.key.id())
