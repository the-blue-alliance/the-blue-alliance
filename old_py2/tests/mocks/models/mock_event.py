from models.event import Event


class MockEvent(Event):

    def __init__(self, week=None, **kwargs):
        super(Event, self).__init__(**kwargs)
        self._week = week

    @property
    def week(self):
        return self._week
