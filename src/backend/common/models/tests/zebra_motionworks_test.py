from google.appengine.ext import ndb

from backend.common.models.zebra_motionworks import ZebraData, ZebraMotionWorks


def test_zebra_motionworks_round_trip(ndb_stub) -> None:
    data: ZebraData = {
        "key": "2019nyny_qm1",
        "times": [0.0, 0.1],
        "alliances": {
            "red": [{"team_key": "frc254", "xs": [1.0, None], "ys": [2.0, None]}],
            "blue": [],
        },
    }
    ZebraMotionWorks(
        id="2019nyny_qm1", event=ndb.Key("Event", "2019nyny"), data=[data]
    ).put()

    zebra = ZebraMotionWorks.get_by_id("2019nyny_qm1")
    assert zebra is not None
    assert zebra.event == ndb.Key("Event", "2019nyny")
    assert zebra.data == [data]
