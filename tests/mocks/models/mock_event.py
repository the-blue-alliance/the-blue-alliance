from models.event import Event


class MockEvent(Event):

    def __init__(self, key_name=None, week=None, year=None):
        self._key_name = key_name
        self._week = week
        self._year = year

    @property
    def key_name(self):
        return self._key_name

    @property
    def week(self):
        return self._week

    @property
    def year(self):
        return self._year
