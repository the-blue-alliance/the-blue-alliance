import base64
import datetime
import json
import pickle

from google.cloud import ndb
from google.cloud.datastore.helpers import GeoPoint

from backend.common.models.award import Award
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.location import Location
from backend.common.models.media import Media
from backend.common.models.team import Team

"""
The purpose of these tests is to make sure that py3 can deserialize cached query results
pickled by the py2 version of the site.

We do a bit of ndb hackery to test it. We start with a base64 encoded cached query, pulled
from the datastore admin tool on prod. We then construct a dummy model (as the value of the
property has already been pickled+compressed for storage) and then round-trip it to a datastore
Entity, to force the ndb library to interpret the raw data as a different model type. This will
let us prove we can deserialize it.

If we do nothing, this fails because the import path of models has changed between py2/py3.
It would fail with a message like:

E       ModuleNotFoundError: No module named 'models'
"""


class RawCachedQueryResult(ndb.Model):
    result = ndb.Property()

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def _get_kind(cls):
        return "CachedQueryResult"


def _run_test(py2_b64_data, expected_result) -> None:
    raw_model = RawCachedQueryResult(
        id="py2_data",
        result=base64.b64decode(py2_b64_data),
    )

    # Check that py3 can load an object written by py2
    raw_entity = ndb.model._entity_to_ds_entity(raw_model)
    query_result = ndb.model._entity_from_ds_entity(
        raw_entity, model_class=CachedQueryResult
    )
    assert query_result.result == expected_result

    # Check that py3 would write an equivalent object and that the round trip
    # returns the same data as the original
    check_query_result = CachedQueryResult(id="py3_data", result=expected_result)
    check_entity = ndb.model._entity_to_ds_entity(check_query_result)
    check_model = ndb.model._entity_from_ds_entity(
        check_entity, model_class=CachedQueryResult
    )

    assert check_model.result == expected_result


class ModelWithInt(ndb.Model):
    int_prop = ndb.IntegerProperty()


def test_round_trip_model_pickle_integer() -> None:
    ModelWithInt(
        id="test_model",
        int_prop=2018,
    ).put()
    model = ModelWithInt.get_by_id("test_model")

    pickled = pickle.dumps(model, protocol=2, fix_imports=True)
    check = pickle.loads(pickled, fix_imports=True, encoding="bytes")

    assert check == model


class ModelWithIntRepeated(ndb.Model):
    int_prop = ndb.IntegerProperty(repeated=True)


def test_round_trip_model_pickle_integer_repeated() -> None:
    ModelWithIntRepeated(
        id="test_model",
        int_prop=[2018, 2019, 2020],
    ).put()
    model = ModelWithIntRepeated.get_by_id("test_model")

    pickled = pickle.dumps(model, protocol=2, fix_imports=True)
    check = pickle.loads(pickled, fix_imports=True, encoding="bytes")

    assert check == model


class ModelWithString(ndb.Model):
    str_prop = ndb.StringProperty()


def test_round_trip_model_pickle_string() -> None:
    ModelWithString(
        id="test_model",
        str_prop="abc123",
    ).put()
    model = ModelWithString.get_by_id("test_model")

    pickled = pickle.dumps(model, protocol=2, fix_imports=True)
    check = pickle.loads(pickled, fix_imports=True, encoding="bytes")

    assert check == model


class ModelWithKey(ndb.Model):
    key_prop = ndb.KeyProperty()


def test_round_trip_model_pickle_key() -> None:
    ModelWithKey(
        id="test_model",
        key_prop=ndb.Key(Media, "test_media"),
    ).put()
    model = ModelWithKey.get_by_id("test_model")

    pickled = pickle.dumps(model, protocol=2, fix_imports=True)
    check = pickle.loads(pickled, fix_imports=True, encoding="bytes")

    assert check == model


def test_round_trip_model_pickle_media() -> None:
    Media(
        id="test_media",
        details_json='{"base64Image": "iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOvwAADr8BOAVTJAAAABl0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC4yMfEgaZUAAAJESURBVFhHzZTBcepAEEQdhYvibCgC8ZHECIQgODoPTiQiq7f0VK3WGCP7sr/qeWZ7e3oH/P9/G4aha0qxJ0qxJ0qxJ0qxJ0qxJ0qxJ0oRxj/6Mbb1/X95Jb8Wp8Hr9dp4JWgL5F0ul1/zl4cYFOoFd8JnwO9f8fgbvMPdYmZupiEqAalxFj/N3m631b3IZTjnO6rzrIekMfsqUGihys99zqVXevaLBT3Eh8X5fG6Ve0c6fp9Jzc+uk+0ez14tyKBgWJWeEHx5RnvF67lUsVowRQYzgD4f5O9b6uqrX71qle2a7zOyDMUkjsfj3HsAfuELkkH1BdE8R+QbqloO//wrzhAfdHiUxYTP0nMW9/u9nVXRHL2VH159280XVBXVgtUHoXcqHY0PRRb4goKZ5tMPBjzQl3SP4FtU//X+OTw+PhazqtJ0x5k74XnPvr3mcXP+Y1F1Mz5B2OPxaGdfhl53/qiosnjL3589NO0wmQjMb1HV4XH8Vc/ZISu/vVyu+RaHyagqNOxLUiGX8Nm8A88in7tfF2zCKCkUs4dQ3ZdL0OcdM55Fnz5ncWjCNKAFWVJ4ID7h4dTUBTOeI3iHt+RzFodZHGWFM0SoL+i+XCx192fWs+XESmjiKPMAj0D6hHudZzNCHi2H132wEsCD8s7RfS7k5/Q7+J/5SnELPKCFDodDw5dN/1ZKcSssczqdFv8Vpe8vlOJf2O12bTmx3+9HqfZtpRR7ohR7ohR7ohR7ohR7ohR7ohR7ohR7ohR7ohT7YXj7BpL35FWepDMDAAAAAElFTkSuQmCC"}',
        foreign_key="avatar_2018_frc999",
        media_type_enum=12,
        private_details_json=None,
        references=[
            ndb.Key("Team", "frc999", project="tbatv-prod-hrd"),
        ],
        year=2018,
    ).put()
    model = Media.get_by_id("test_media")

    pickled = pickle.dumps(model, protocol=2, fix_imports=True)
    check = pickle.loads(pickled, fix_imports=True, encoding="bytes")

    assert check == model


def test_round_trip_model_pickle_event_team() -> None:
    k = EventTeam(
        id="2020test_frc254",
        team=ndb.Key(Team, "frc254"),
        event=ndb.Key(Event, "2020test"),
    ).put()
    model = k.get()

    pickled = pickle.dumps(model, protocol=2, fix_imports=True)
    check = pickle.loads(pickled, fix_imports=True, encoding="bytes")

    assert check == model


def test_cached_result_team_year_media() -> None:
    py2_b64 = b"""
eJy1VcuP5EYd3pmdMJNk0aIoKKQlJGtEpCW9M3612/aKi9ttt/vpfrjdDwWNyna57W6/Xe6HIxBEnBBHzhzgX+DAH4CExA0JDhESkbhzisSZ6tnJjjRZknCgJbvtqq++71dfVX3+2emP05Nndhg7MMivQ+j44K3+7T09/eHP08fG+288erQW1t/Jf4osgLZXSRY7V17mZD94+503bpGX74MtQCC7uftjKFq4cTNbFMUn2QeVt904g/4qutnAA/How3cr73wZl71XeXqrfYMOCbyBURFi6OnFk4yrvJVBF2YwsmFOnHz4gf3lUvLyzIAg/OXJt16yISf7duXsAEGGSR5f/PNp+b2L88q5nUGAoIPb3rz4xee/+/Vvfv/pafnZ+cXTyhMHIuAH+c06jyPc/+fzyp/OP760QA7rtXYIVvDyBXHpmw19vKO6rVUs4d9gMvWU6Qo/ycebFMvS4vjSJzMPHRsaLadhTBVJ6rWGMrn3GqNja7CbqEGJH/TtTpKamdDQJdPo3A4IqLHpUVNGDB3N8exwKtktNbGiUWGFJtVujoq+XDv0XWUFllM8oKNMpuOGqXpauTQaNkwkRRk53mLrW/JKFpaaIrdHK70ZDw1/5Ke8S5lddtaSh3yekSmcLXnIxho5FMlWDXiASved117xeL8m633Losm5yHUsYZYIWiY6Sa0zW/U4lSoCmiyDmr1Q9Vh1hE6000VXcFfWtj90FuGySHwllUCwV9fkgA3rLG2x7aWxjvR6VmZtuOm7eTpt+d4hF8UyNedwC3oNg1U8Yc65rboJKbvuJmKntKvFpkrBkq6hQ7exmnVmUNH23DjaqnU+mOZmvBuPFuWqWXM5XbTqRZrNeToNIAP4Uj80+9PNOnfXrJZLbqH0NhuNbjiKMK6OrDSIdZLcZaUnuY7mT/cLY0hF/ZlIFmJkzsdajzE1mhMZgZqbjbm5QlMtntuptqCG47FVW8XdJYf6w8a6HAXsZFhT0ZQk51Xd2FWHHihT1KH23IavzaPhNmNDez6sLmiV7pdcg9GHe9ByXC/gWDL14zxa91hOEAc6tQtH675Fa2ZtrgmmTS7bk4LcmoeiOgbaAazSgb7vTf3WXBiEgiQIfsQjV2VKuStvpnnNGbFLp0fpttPnODUquciereVBV1JnZqfWbvJezTGmDUOHbdbXUHVcqrGz1FoztU9N4l7Vr87lPS0y7iyvzpVJuPa7w760ppp1TyucZTmQNZ/RaJbZKbncFHJ+7E74DUeO+GqH5CaR0ht2ZbUZO80d5wxIetm1J3lul6mjbgUzgcI20Dsuo9OMZYR7tipqqbtEyXjMx97XXQa/mK/5RoKtUmcwafabx2MkKYFqbCbFKJTly5+Ulcq7SebjyIE3D475o5e5UCTOq1z47V0ufHLyjeLN8o4heWb84TEOyR+9JiSfvWL5/ioDlg2cm3znI9uzgL25Qji1rjDPFf0ke/YwKN+rfPe10P+WlW/+v7Lyj3/91d8+/fe/TsvPz16Tlf84q/z97OPL2w8INji3Mz9BfhwdE/OoRGAR4ugZkcVWjAgbBAEmnrya2jVhePCuc4cpEX5rR06Ro8wHAdGEOfaEkHYgc4g8iaMcu+QQ1oFowQhmGNGPUZzlBEDEQCGa/nGcjQgNZAgb6hDKFkbompCCPH5+S35bFbA9H24xEYoJC+LewAfYNqKOC0zwBKMj3xH9kOij6KPovmA7DhN4NOqB+gy7l1lFdng56vlXlIb74I5QolUAIuceJHsgTLCPuecnzwnZINT2eGIQE4SZifFR3LfzB6gjQQMgFEAZK9Pi9eVz4m5l/C++Yh5CSf6CJB0G0fsUrmNXLJB9bQdx4bhZjGcYQUTiZYQQs8YoJxMsRLIcL4o1GkJbqIkcT7k24BgWUJTl8g4rWKSN1+d6nazuJe/20FGUoRjqimauGNFg6Bcc/4KuLe+BEQhvS7vfE8QXO+d/Pb9/udurn5x845Nnwev/AHH18gw=
            """.strip()
    expected_result = [
        Media(
            key=ndb.Key(
                "Media",
                "avatar_avatar_2018_frc999",
                project="tbatv-prod-hrd",
            ),
            created=datetime.datetime(2018, 2, 20, 10, 0, 48, 320900),
            details_json='{"base64Image": "iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOvwAADr8BOAVTJAAAABl0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC4yMfEgaZUAAAJESURBVFhHzZTBcepAEEQdhYvibCgC8ZHECIQgODoPTiQiq7f0VK3WGCP7sr/qeWZ7e3oH/P9/G4aha0qxJ0qxJ0qxJ0qxJ0qxJ0qxJ0oRxj/6Mbb1/X95Jb8Wp8Hr9dp4JWgL5F0ul1/zl4cYFOoFd8JnwO9f8fgbvMPdYmZupiEqAalxFj/N3m631b3IZTjnO6rzrIekMfsqUGihys99zqVXevaLBT3Eh8X5fG6Ve0c6fp9Jzc+uk+0ez14tyKBgWJWeEHx5RnvF67lUsVowRQYzgD4f5O9b6uqrX71qle2a7zOyDMUkjsfj3HsAfuELkkH1BdE8R+QbqloO//wrzhAfdHiUxYTP0nMW9/u9nVXRHL2VH159280XVBXVgtUHoXcqHY0PRRb4goKZ5tMPBjzQl3SP4FtU//X+OTw+PhazqtJ0x5k74XnPvr3mcXP+Y1F1Mz5B2OPxaGdfhl53/qiosnjL3589NO0wmQjMb1HV4XH8Vc/ZISu/vVyu+RaHyagqNOxLUiGX8Nm8A88in7tfF2zCKCkUs4dQ3ZdL0OcdM55Fnz5ncWjCNKAFWVJ4ID7h4dTUBTOeI3iHt+RzFodZHGWFM0SoL+i+XCx192fWs+XESmjiKPMAj0D6hHudZzNCHi2H132wEsCD8s7RfS7k5/Q7+J/5SnELPKCFDodDw5dN/1ZKcSssczqdFv8Vpe8vlOJf2O12bTmx3+9HqfZtpRR7ohR7ohR7ohR7ohR7ohR7ohR7ohR7ohR7ohT7YXj7BpL35FWepDMDAAAAAElFTkSuQmCC"}',
            foreign_key="avatar_2018_frc999",
            media_type_enum=12,
            private_details_json=None,
            references=[
                ndb.Key("Team", "frc999", project="tbatv-prod-hrd"),
            ],
            updated=datetime.datetime(2018, 2, 20, 10, 0, 48, 320930),
            year=2018,
        ),
        Media(
            key=ndb.Key(
                "Media",
                "grabcad_switchback-team-999-1",
                project="tbatv-prod-hrd",
            ),
            created=datetime.datetime(2020, 12, 30, 21, 58, 14, 901316),
            details_json='{"model_description": "Team 999 2018 robot called Switchback. The robot won the Industrial Design Award sponsored by General Motors at NE District Hartford Event. Also, the Team achieved to be Alliance 6 captain at the  Hartford Event.\\n\\nThe robot competed at NE District Waterbury Event, NE District Hartford Event, New England District Championship, CT FIRST State Robotics Championship, and BattleCry 19.", "model_image": "https://d2t1xqejof9utc.cloudfront.net/screenshots/pics/3579941eec849570fca523a00bf7d38b/card.jpg", "model_created": "2020-12-29T21:57:14Z", "model_name": "Switchback Team 999"}',
            foreign_key="switchback-team-999-1",
            media_type_enum=9,
            private_details_json=None,
            references=[
                ndb.Key("Team", "frc999", project="tbatv-prod-hrd"),
            ],
            updated=datetime.datetime(2020, 12, 30, 21, 58, 14, 901329),
            year=2018,
        ),
    ]
    _run_test(py2_b64, expected_result)


def test_cached_result_team_social_media() -> None:
    py2_b64 = b"""
eJyVkLFKxEAURZO4kphdUMKCMtUiKriwK4iI1tZ228owm3mJEzOT5M1kISlE7fQL/AELCz/JT7C1NjuITSqbV9x7OFzeg3dTubEsOOR6LoELFl7bW3nHj9XGgrqOk11lO/reLJlZzUos+OwWOZ4Mo01L7h8IpQ1Lkcl1m4gcqBGGKVFLI1JAfXZxejnCQzJMCgSRKnoHzcSZjknU53CXbNsZ1DQlUFC17FAv8PGchAgJIKgY9MSdHsX9VbodLIDJF9dPMF7rDMeQDBpg2Fmcdi/wiR8jMAO8C7aC1+/n94/PL6+NyIiDYSLXNNOFsjQh4xLFqoNpr7OmuuR/prdf05P7388s2fwH/A+AHg==
            """.strip()
    expected_result = [
        Media(
            key=ndb.Key(
                "Media",
                "instagram-profile_titaniumtigers4829",
                project="tbatv-prod-hrd",
            ),
            created=datetime.datetime(2020, 12, 20, 20, 3, 17, 962520),
            details_json=None,
            foreign_key="titaniumtigers4829",
            media_type_enum=7,
            private_details_json=None,
            references=[ndb.Key("Team", "frc4829", project="tbatv-prod-hrd")],
            updated=datetime.datetime(2020, 12, 20, 20, 3, 17, 962533),
            year=None,
        )
    ]
    _run_test(py2_b64, expected_result)


def test_cached_result_team_year_events() -> None:
    py2_b64 = b"""
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
    """
    expected_result = [
        Event(
            key=ndb.Key("Event", "2020arli", project="tbatv-prod-hrd"),
            city="Little Rock",
            country="USA",
            created=datetime.datetime(2019, 9, 4, 22, 59, 12, 341024),
            custom_hashtag=None,
            district_key=None,
            enable_predictions=False,
            end_date=datetime.datetime(2020, 3, 7, 23, 59, 59),
            event_short="arli",
            event_type_enum=0,
            facebook_eid=None,
            first_code=None,
            first_eid="44122",
            name="Arkansas Regional",
            normalized_location=Location(
                city="Little Rock",
                country="United States",
                country_short="US",
                formatted_address="2600 Howard St, Little Rock, AR 72206, USA",
                lat_lng=GeoPoint(34.7232243, -92.2989882),
                name="Arkansas State Fair",
                place_details=json.loads(
                    '{"rating":4.1,"reference":"ChIJeWa8jDO70ocRagHspTnFpRk","place_id":"ChIJeWa8jDO70ocRagHspTnFpRk","plus_code":{"global_code":"8669PPF2+7C","compound_code":"PPF2+7C Little Rock, Big Rock Township, AR, United States"},"formatted_address":"2600 Howard St, Little Rock, AR 72206, USA","id":"1b0183fca2c5b5ac2ab4ecd870974709e1380d70","formatted_phone_number":"(501) 372-8341","opening_hours":{"weekday_text":["Monday: 9:00 AM \\u2013 4:00 PM","Tuesday: 9:00 AM \\u2013 4:00 PM","Wednesday: 9:00 AM \\u2013 4:00 PM","Thursday: 9:00 AM \\u2013 4:00 PM","Friday: 9:00 AM \\u2013 4:00 PM","Saturday: Closed","Sunday: Closed"],"open_now":false,"periods":[{"close":{"day":1,"time":"1600"},"open":{"day":1,"time":"0900"}},{"close":{"day":2,"time":"1600"},"open":{"day":2,"time":"0900"}},{"close":{"day":3,"time":"1600"},"open":{"day":3,"time":"0900"}},{"close":{"day":4,"time":"1600"},"open":{"day":4,"time":"0900"}},{"close":{"day":5,"time":"1600"},"open":{"day":5,"time":"0900"}}]},"vicinity":"2600 Howard Street, Little Rock","scope":"GOOGLE","website":"http://www.arkansasstatefair.com/","utc_offset":-300,"user_ratings_total":845,"photos":[{"width":7218,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/116496628514619014671/photos\\">Jeffrey Ruthven</a>"],"photo_reference":"CmRaAAAAfS4wDZ_Dz2zaOegt0II3nrVyVxs9yibWt8lRLVEsSZ29eTGHyNVpiELkluMwlnPVMFBVJBDqOB-V4fPqPSud3MHLr0xf1tOzAfzxjFPELjG2PC8-9fngvbloWiqo4rnLEhArLjggwKOsRTZxEUIYfAQeGhTw7z-XS-Hz0SZgdNHpJFys5bis0Q","height":2217},{"width":4032,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/117281484685886467569/photos\\">Reagan B.</a>"],"photo_reference":"CmRaAAAAaXcbGWZaBYGMwMCBiIlQQOhRabKe4tKqC3qKt123tjYHzxhxfKnZkAr0bjLJv075KsO1Z-o8S14CSRRkhxRtpCAznASd6VCDRLj_PVUlAxFGcy3GZUOi8W9S3xW19zblEhA4Bb2rYHIhSBwydXnQPvdkGhRnFBv4kvMUngqgdsZFzOM7FQW0xQ","height":3024},{"width":5312,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/114322659397982878243/photos\\">Shawna Satchell</a>"],"photo_reference":"CmRaAAAADYp13PsMiHMiv1jj1UL2THPEOITDl-cYZGWxxfssXOjwueSg6aQiI8HV7TtpEdyCltPGJrgeCWNwpT4zyBeJnDHhkY7j1JFr1D7WyT-QCzNNjc_dEzWudyvHXuFVA9mcEhA5jyRZhZpN8auCh5V3Xdj_GhTOqK0U2IVNGA-os4P56Jl_flvrVA","height":2988},{"width":3264,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/106378446157399905887/photos\\">Birdie Haynes</a>"],"photo_reference":"CmRZAAAARjCqWLMhpQ5LQd-d_0q317B5AUKhMRVgKsNJ49J-mBeGNHe_8Ao6fyYXYNp3NPbF-BaGquD3Iyij3H8qdF3eeuwVjxpxZftJEjPcUMoRpV6N5i96rOjYJWKj3--kWqA9EhBQWngYemeK6_WDyNy7XFlNGhSN3kAqE6BpnwLurxM1usIcLpmdJg","height":1836},{"width":2048,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/117814741388408667095/photos\\">Gilbert Navarro</a>"],"photo_reference":"CmRaAAAAft1qWMDqyggxG5arbtXpVlwTVBNRMv7wxcv8h90z8QFv_f859ErvjXXK0bg-Jz6Mxn50PyhJyeViJ9JCj6mZdPR5e1oyNqUYFPvU_JMickmYMBfZ0gQvJ5po5M_ojURUEhDUI5PGxKryMmzz-3o3OjFgGhTuR1oMfrDaLqkjfyk_Mvoxp38mYA","height":1152},{"width":3000,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/106462081222341217197/photos\\">Mario Hoof</a>"],"photo_reference":"CmRaAAAA82EqiSaHMkWVP4Xbz7HejLZcB42oYwKrQieJCuwhkU09L-pDOZrpccYa4Hq05Ci6WXX4jddytPlOEknp18-nRNqgAW-reULqN4wTfu8gLuKYd3GzUua0iPFlERKc05xJEhCVMXG2_6zzzuGobsYQO6cZGhSg3J8hnUFl7vbHrFdcs2BoKTGZ4g","height":4000},{"width":1920,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/111131212365154471728/photos\\">Moon Light</a>"],"photo_reference":"CmRaAAAAr4g1kTt9r9hOhyEXskUAYaXhNRYlE0_S9wJ1yKrAP1rBc-q0ucUP68ROFeyZZHUvB1M8x8cyDiybvy-kb4RDcmy1vHjiSWCDG6okif2oAZiGamg22rsdx_56d57A3i9UEhBYeMt_sHAs_7C4tnEOdXpRGhTusRc9wbSyLQp_P5QbuZfrkbq0tA","height":1088},{"width":3120,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/118248371877587310684/photos\\">Henry Voss III</a>"],"photo_reference":"CmRaAAAAiOiKmZac4bkc7E1RbMlMh0wy_iaJ8IJ2yVch89Stfy7ZxtBoDkWdByd4YUZBMEV_0rw2IYj1AjnVde3h0N1kALzgYYUu6hPwMdhjakqWw5kJWVInmfTURmg9R83sdDxNEhARMloYBpJGBqNRyA7QCxv7GhR3fs34PIIU92G3R1ZFlM4N_o1Png","height":4160},{"width":4128,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/106584388131481493796/photos\\">Ser Dee</a>"],"photo_reference":"CmRaAAAAM_EbRQundYMv9nbZ-hE8jBRVp-nwJEfFIIV0GWO_DkwSfDw8Jr6FSdLZ6kBpM8VWG4dqzLK1apw1Cm3ApmKJe-PRmwLL1v9ngmCE_XkYRYhwOvmCcrzWFngBl_q3wtmJEhCyzuPcWfrIB0kPzygSGMlBGhSYV9kUy_wsK1JMsNLvpv-kxiupQg","height":3096},{"width":4048,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/115844871752550033150/photos\\">Roderick Wells</a>"],"photo_reference":"CmRaAAAAEJW1-CeuDujwTkHTBBDQO08hKuLIW3y__ncvcqhWR2tGyAyyVDwG_SITBOBFDfw1kQGvWKCdXGvsS0BkQiniOT7CnV-2uuTVD7LRgCrcQHs6oCsJE23Qk7c4efUWWTMDEhD2Iuzw8thO9x5TqEGADDBrGhQzkGalFm9uxHi-ZIDRuDJs1AsOew","height":3036}],"types":["point_of_interest","establishment"],"icon":"https://maps.gstatic.com/mapfiles/place_api/icons/generic_business-71.png","name":"Arkansas State Fair","url":"https://maps.google.com/?cid=1848100073492971882","adr_address":"<span class=\\"street-address\\">2600 Howard St</span>, <span class=\\"locality\\">Little Rock</span>, <span class=\\"region\\">AR</span> <span class=\\"postal-code\\">72206-1714</span>, <span class=\\"country-name\\">USA</span>","international_phone_number":"+1 501-372-8341","reviews":[{"rating":5,"author_name":"Ms. Bridge","language":"en","text":"We attended the Vintage Market Days, and they were wonderful! So many beautiful and crafty items! The restrooms weren\'t near as gross as I expected. The Management crew was extremely helpful. Part of the proceeds from the event go to support Lifeline; which helps people overcome addiction, grief, depression, etc.","relative_time_description":"3 months ago","author_url":"https://www.google.com/maps/contrib/102599242064693255919/reviews","time":1557628493,"profile_photo_url":"https://lh3.googleusercontent.com/-a9bRXF3Gi2U/AAAAAAAAAAI/AAAAAAAAAAA/ACHi3rdVBcZ4NqWyn8pt1m_l0Vz7cWditQ/s128-c0x00000000-cc-rp-mo-ba5/photo.jpg"},{"rating":5,"author_name":"Anita Harris","language":"en","text":"I go for the food, which is awesome \\ud83d\\ude0aKids go for the rides and meet up with friends..","relative_time_description":"in the last week","author_url":"https://www.google.com/maps/contrib/114198378663497679597/reviews","time":1567565590,"profile_photo_url":"https://lh3.googleusercontent.com/-94BAfXUYe9Y/AAAAAAAAAAI/AAAAAAAAAAA/ACHi3rd2jHuweo7sLRr4a2_ug6qNARXcfQ/s128-c0x00000000-cc-rp-mo/photo.jpg"},{"rating":5,"author_name":"margaretrobinson robinson","language":"en","text":"i  love it  because  they  have  lots  of  hair  products  lots  cheaper  and  its  only  a  few  blocks  away from  where i  live.","relative_time_description":"a month ago","author_url":"https://www.google.com/maps/contrib/118232699470771851326/reviews","time":1562697203,"profile_photo_url":"https://lh5.googleusercontent.com/-2eOur8Jw7qc/AAAAAAAAAAI/AAAAAAAAAAA/ACHi3reeNgGIC1jOw1NY_Zm1IRZqR5hu0g/s128-c0x00000000-cc-rp-mo/photo.jpg"},{"rating":5,"author_name":"Tonya Bartlett","language":"en","text":"Gun show with the husband. He enjoyed.","relative_time_description":"in the last week","author_url":"https://www.google.com/maps/contrib/106270177367724970333/reviews","time":1567462706,"profile_photo_url":"https://lh3.googleusercontent.com/a-/AAuE7mDSSRz5a1i3_vENk0LEjIkY4oUICAFXb5ZDC8gkI_8=s128-c0x00000000-cc-rp-mo-ba5"},{"rating":4,"author_name":"Heath Barrentine","language":"en","text":"Fun time for the family but not always the greatest area of town.","relative_time_description":"a month ago","author_url":"https://www.google.com/maps/contrib/112560151191348675551/reviews","time":1562643285,"profile_photo_url":"https://lh3.googleusercontent.com/a-/AAuE7mAMsgmzJG8PgU3TKHE16r3D1MrN0gr5_PY8a-uIsoo=s128-c0x00000000-cc-rp-mo-ba4"}],"geometry":{"location":{"lat":34.7232243,"lng":-92.2989882},"viewport":{"northeast":{"lat":34.7246191802915,"lng":-92.29764246970849},"southwest":{"lat":34.7219212197085,"lng":-92.3003404302915}}},"address_components":[{"long_name":"2600","types":["street_number"],"short_name":"2600"},{"long_name":"Howard Street","types":["route"],"short_name":"Howard St"},{"long_name":"South End","types":["neighborhood","political"],"short_name":"South End"},{"long_name":"Little Rock","types":["locality","political"],"short_name":"Little Rock"},{"long_name":"Big Rock Township","types":["administrative_area_level_3","political"],"short_name":"Big Rock Township"},{"long_name":"Pulaski County","types":["administrative_area_level_2","political"],"short_name":"Pulaski County"},{"long_name":"Arkansas","types":["administrative_area_level_1","political"],"short_name":"AR"},{"long_name":"United States","types":["country","political"],"short_name":"US"},{"long_name":"72206","types":["postal_code"],"short_name":"72206"},{"long_name":"1714","types":["postal_code_suffix"],"short_name":"1714"}]}'
                ),
                place_id="ChIJeWa8jDO70ocRagHspTnFpRk",
                postal_code="72206",
                state_prov="Arkansas",
                state_prov_short="AR",
                street="Howard Street",
                street_number="2600",
            ),
            official=True,
            parent_event=None,
            playoff_type=None,
            postalcode="72206",
            remap_teams=None,
            short_name="Arkansas",
            start_date=datetime.datetime(2020, 3, 4, 0, 0),
            state_prov="AR",
            timezone_id="America/Chicago",
            updated=datetime.datetime(2020, 8, 2, 9, 0, 28, 56407),
            venue="Arkansas State Fairgrounds - Barton Coliseum",
            venue_address="Arkansas State Fairgrounds - Barton Coliseum\nBarton Coliseum\n2600 Howard Street\nLittle Rock, AR 72206\nUSA",
            webcast_json='[{"type": "twitch", "channel": "firstinspires3"}, {"type": "twitch", "channel": "firstinspires4"}]',
            webcast_url=None,
            website="http://www.firstinspires.org",
            year=2020,
        ),
        Event(
            key=ndb.Key("Event", "2020lake", project="tbatv-prod-hrd"),
            city="Kenner",
            country="USA",
            created=datetime.datetime(2019, 9, 4, 22, 59, 12, 343527),
            custom_hashtag=None,
            district_key=None,
            enable_predictions=False,
            end_date=datetime.datetime(2020, 3, 28, 23, 59, 59),
            event_short="lake",
            event_type_enum=0,
            facebook_eid=None,
            first_code=None,
            first_eid="43914",
            name="***SUSPENDED*** Bayou Regional",
            normalized_location=Location(
                city="Kenner",
                country="United States",
                country_short="US",
                formatted_address="4545 Williams Blvd, Kenner, LA 70065, USA",
                lat_lng=GeoPoint(30.0395012, -90.2405773),
                name="Pontchartrain Convention & Civic Center",
                place_details=json.loads(
                    '{"rating":4,"reference":"ChIJS8lOpca2IIYRlv0DNS1IJAs","place_id":"ChIJS8lOpca2IIYRlv0DNS1IJAs","plus_code":{"global_code":"862F2QQ5+RQ","compound_code":"2QQ5+RQ Kenner, 3, LA, United States"},"url":"https://maps.google.com/?cid=802845992578973078","formatted_address":"4545 Williams Blvd, Kenner, LA 70065, USA","id":"c7d001e0f32dd128c2a10c8b64144d99f2f18429","vicinity":"4545 Williams Boulevard, Kenner","scope":"GOOGLE","website":"http://www.pontchartraincenter.com/","utc_offset":-300,"user_ratings_total":29,"photos":[{"width":2048,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/106589631940773219639/photos\\">Pontchartrain Convention &amp; Civic Center</a>"],"photo_reference":"CmRaAAAAQ4ezrzxBiJgV3_L7f_VbBb6PTc572Xlz5lElD7laqoG-uLEGUL2ESgt4d3bOCL27Yqj5pK8hhKY7eJCTv_Wb8rasy6ZjlMpLTSYkb_u99vPz-hyo2qCJB_-h3K3Lff9LEhDnT9sReTf4dFanakbs5UdNGhQS7wWA0rr1WV6-FpY1cXeAGz20bw","height":1334},{"width":3456,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/106589631940773219639/photos\\">Pontchartrain Convention &amp; Civic Center</a>"],"photo_reference":"CmRaAAAA8ftpy0Uz6jZuR6IF3k4-VF4gsG1023pjjreOTMZqroQq0Wh02NmCshEYKZNYVg65eLFuyYzETomPS61w-_5UT_anHesKXDoJcmn861yi5mt30j7bK-HRLCvlOE0KCpXCEhDlpT7TMzQZAfhC4ASiifSTGhTCI4S4YV2i5z_vBM-LmEpRL4jR_A","height":2304},{"width":1368,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/106589631940773219639/photos\\">Pontchartrain Convention &amp; Civic Center</a>"],"photo_reference":"CmRaAAAAKJsJYbAHnBF_AZZUk6SoY0HsjlO90R2WW47IrzV9rZVYS6Q5uveBM5jwe6536tfagR5HhyA45CPZXh3S9TgOuCTxRGpheNSfSCD7ag5CXub0uAvbspQN-0GurNEzGiv0EhAJJ4jbaN_wLPMTG7QmUfGfGhSZW4h8N_K69wUN8VmXlD34yEYE3Q","height":1365},{"width":2560,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/118318046516796101920/photos\\">MGTOW YOJOA84</a>"],"photo_reference":"CmRaAAAAC0T1WTXZ2xyTdbtl62BFP01fB_A1QlzPlTlTlAXP_P7Csy0U0iLbeTRcqd2dRfdUUoikjDjOTrGsOIjUqL7ykIkxeTaiYEkgbV50TuvqTVVrYmwm_Lq7PWcHkg4Lm_6sEhD9XUu6N20sqBgYubbAQQifGhToye0ToC6gCZpJxDYumpOc7vW_VA","height":1440},{"width":1024,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/106589631940773219639/photos\\">Pontchartrain Convention &amp; Civic Center</a>"],"photo_reference":"CmRaAAAANLmbPSCDu2WhtC_E-W_iY5nQYOIAqi5CQGWFKaPoF2jkOCLxTpTFhmlA0sW6jRvLcaDpuf3Q-Mg3VzhEZBT5VMN3sSJwIFNMiMnD6Nc05N5Z7dMEIUb0-D9e-HIhcx0rEhA6BCjWi_uIf5qxGIZHtO50GhTDHMHfd1tIIwpMMBtNgid02eBbag","height":768},{"width":640,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/106589631940773219639/photos\\">Pontchartrain Convention &amp; Civic Center</a>"],"photo_reference":"CmRaAAAAgCIY37j5HApMbJsIv7QzUt3MO3aWTY4TdCsvAUBrff_ar-eK_xcFuzGLgowI_awvPu__7scuIJHU0_r1kDPVKsfWF6PJo2X5PsBjLBgF36ZgP2nj-D3JI6e4UUw3UqPgEhDnFM4x0aWFlnyBj7Rx1eWOGhQWX8AK65u2AU7SkOzJXHTL1rm26w","height":480},{"width":3456,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/106589631940773219639/photos\\">Pontchartrain Convention &amp; Civic Center</a>"],"photo_reference":"CmRaAAAAdaOVFj0fuGpguQI5gh1_ori1f3WnfU2yA-aoFsZUUL9kVD0ry0NZqOl_1mzvEnKBJZFyuZ13pUwqqikccRa2YJHBLcNJJP5LjDRwTdP_nS2A7IICJPd6KiqZDMthjHIhEhAvPd-3biISOnR4tifDvDsIGhR3BXVkugaoSzUhQtRF_bnXN8HeVA","height":2304},{"width":1530,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/106589631940773219639/photos\\">Pontchartrain Convention &amp; Civic Center</a>"],"photo_reference":"CmRaAAAAosMb_JHIvB8mc1tjo5LaihPvLAeEu0qPne_8gnoTM8fybVQUvOwx18LT24owcDDSTmDrWgFzfn4LQu4iXreetRcU6UPMkg9LksA3ZldkAM6kRFhOyti7xucN1Ftq9Xf1EhCeFsmSTS9Q1dcxGaohtT9qGhSvTW1HNiNGMJ6xkf_vMs1oob_LvA","height":1020},{"width":4032,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/114059648357239814898/photos\\">Thearl S Cockerhm Sr</a>"],"photo_reference":"CmRaAAAAjwvZMG6ebC76duhHkIEGa1khYNNglg1EQJ95TBn1wgBluibvH9vR0sMg3IkhrrZEuEyI66da6_RpCTZfEzPFrLXITjtbh5Y_DVOQ1mE-vEs8wOucY4Kmad8hO_QgWTjYEhC5Go0KEtkLEC0TW2ej30tnGhRzAE8sb-hhdgano5f5SnchNlVcZA","height":3024},{"width":5184,"html_attributions":["<a href=\\"https://maps.google.com/maps/contrib/106589631940773219639/photos\\">Pontchartrain Convention &amp; Civic Center</a>"],"photo_reference":"CmRaAAAAI-izX5lOK22rnzekj62upp5QJljems1JtdL_uOTlJDhN5oq8dtbhd5ykrRW3ojTgq8IPjZZI2Zvhmyj4_DkSSM5W3LbMSQ-sUh9mjHH71yUUMLuIAb2Cg_wFfs1veuD2EhBzstNBofYsTBIyUN2oHmU2GhSZfIMrB4MtI86YchCkeH8ixOGQAg","height":3456}],"types":["point_of_interest","establishment"],"icon":"https://maps.gstatic.com/mapfiles/place_api/icons/generic_business-71.png","name":"Pontchartrain Convention & Civic Center","geometry":{"location":{"lat":30.0395012,"lng":-90.2405773},"viewport":{"northeast":{"lat":30.0410345302915,"lng":-90.23918276970849},"southwest":{"lat":30.0383365697085,"lng":-90.2418807302915}}},"adr_address":"<span class=\\"street-address\\">4545 Williams Blvd</span>, <span class=\\"locality\\">Kenner</span>, <span class=\\"region\\">LA</span> <span class=\\"postal-code\\">70065-1449</span>, <span class=\\"country-name\\">USA</span>","international_phone_number":"+1 504-465-9985","reviews":[{"rating":3,"author_name":"J Hall","language":"en","text":"Security for high school graduations needs to be much better! Far too many out of control people disrupting graduation ceremonies. In spite of the fact that there are inspections of bags and things brought into the center people are somehow still able to smuggle fans air horns and some and some things that are supposedly banned. None of those people were thrown out for being overly disruptive. Tends to take away some solemn nature of a graduation ceremony. Very frustrating because sometimes parents can\'t even hear their own child\'s name called when they go to receive their diploma. Pontchartrain Center has to do more in terms of security and removal of those people that turn what should be a pleasant experience into a mockery of what the graduation ceremony really should be.","relative_time_description":"3 months ago","author_url":"https://www.google.com/maps/contrib/113479284789838083851/reviews","time":1558670746,"profile_photo_url":"https://lh3.googleusercontent.com/-P6WqhD_rcDA/AAAAAAAAAAI/AAAAAAAAAAA/ACHi3rdnY9crncADQi7Fn95fqUfoH3UJNA/s128-c0x00000000-cc-rp-mo/photo.jpg"},{"rating":4,"author_name":"Barry Miller","language":"en","text":"We had a terrific time at the Pontchartrain Center to see the Lego convention. Plenty of spectators, adults and kids.\\nLots of exhibits showing amazing Lego constructions, from Carnival in New Orleans, to a Space Shuttle launch; even a Lady Gaga concert.\\nSure, there was lots of mechanise available for purchase, but for the afficionato of those little building blocks, the choices seemed almost endless.\\nThe attention to detail in the art of the Lego is truly amazing to see, and it was fairly easy to do at the Pontchartrain Center. Plenty of space inside, so it never felt crowded.\\nThe center is easy to get to. Off the Interstate, all the way up Williams, and a left turn. Huge parking lot beyond the building.\\n\\nCarnival Balls are good here too, but that\'s another story...","relative_time_description":"7 months ago","author_url":"https://www.google.com/maps/contrib/110018269724028741153/reviews","time":1549402678,"profile_photo_url":"https://lh3.googleusercontent.com/a-/AAuE7mC6XOgLmJugb8B3pmDliY3eITynycMYlnI4bnRmMjc=s128-c0x00000000-cc-rp-mo-ba4"},{"rating":1,"author_name":"Jordan Mendez","language":"en","text":"The staff was rude more than once, item was removed from a diaper bag. Said we could retrieve it when we left. They then magically lost it. Likely someone took it. Thanks","relative_time_description":"3 months ago","author_url":"https://www.google.com/maps/contrib/103168975509275716123/reviews","time":1558302497,"profile_photo_url":"https://lh5.googleusercontent.com/-V2-5TYWgf_Y/AAAAAAAAAAI/AAAAAAAAAAA/ACHi3rc8Oe8lrZik-AgysMSIEg4YzBa0nQ/s128-c0x00000000-cc-rp-mo/photo.jpg"},{"rating":5,"author_name":"Thearl S Cockerhm Sr","language":"en","text":"Safe place in kenner","relative_time_description":"2 months ago","author_url":"https://www.google.com/maps/contrib/114059648357239814898/reviews","time":1561328105,"profile_photo_url":"https://lh3.googleusercontent.com/a-/AAuE7mC4vHbyv-cTLaJhYI5Hy-kUlIVYC9LSLlScYit79g=s128-c0x00000000-cc-rp-mo-ba4"},{"rating":4,"author_name":"D Schnatz","language":"en","text":"Holiday Daze Arts and Crafts show. Was supposed to be 100+ booths. In actuality, was more like 60-75.","relative_time_description":"10 months ago","author_url":"https://www.google.com/maps/contrib/109352164542507798268/reviews","time":1541356366,"profile_photo_url":"https://lh3.googleusercontent.com/a-/AAuE7mCESjuCTRJH2F8zA9bcv42fstwL7mKZkRfnLa69sQ=s128-c0x00000000-cc-rp-mo-ba5"}],"formatted_phone_number":"(504) 465-9985","address_components":[{"long_name":"4545","types":["street_number"],"short_name":"4545"},{"long_name":"Williams Boulevard","types":["route"],"short_name":"Williams Blvd"},{"long_name":"Kenner","types":["locality","political"],"short_name":"Kenner"},{"long_name":"4","types":["administrative_area_level_3","political"],"short_name":"4"},{"long_name":"Jefferson Parish","types":["administrative_area_level_2","political"],"short_name":"Jefferson Parish"},{"long_name":"Louisiana","types":["administrative_area_level_1","political"],"short_name":"LA"},{"long_name":"United States","types":["country","political"],"short_name":"US"},{"long_name":"70065","types":["postal_code"],"short_name":"70065"},{"long_name":"1449","types":["postal_code_suffix"],"short_name":"1449"}]}'
                ),
                place_id="ChIJS8lOpca2IIYRlv0DNS1IJAs",
                postal_code="70065",
                state_prov="Louisiana",
                state_prov_short="LA",
                street="Williams Boulevard",
                street_number="4545",
            ),
            official=True,
            parent_event=None,
            playoff_type=None,
            postalcode="70065",
            remap_teams=None,
            short_name="Bayou",
            start_date=datetime.datetime(2020, 3, 25, 0, 0),
            state_prov="LA",
            timezone_id="America/Chicago",
            updated=datetime.datetime(2020, 5, 4, 9, 0, 12, 325184),
            venue="Pontchartrain Center",
            venue_address="Pontchartrain Center\n4545 Williams Blvd\nKenner, LA 70065\nUSA",
            webcast_json='[{"type": "twitch", "channel": "firstinspires7"}, {"type": "twitch", "channel": "firstinspires8"}]',
            webcast_url=None,
            website="http://www.frcbayouregional.org",
            year=2020,
        ),
    ]
    _run_test(py2_b64, expected_result)


def test_cached_result_district() -> None:
    py2_b64 = b"""
eJzNmk1vG0UYx5NQEUMDRBWqKp/CnqByq52XfcuZIPVaekOVtba3dFt7naw3qZIoCLjzGfoZkCrBgQu3fgC+AFLFBXFFHNmZEHu0z2bn73WIevPL+Bn/5nmZ/8w+324MJ9NRMp7dH6WzIk+HxfufX7w4WP/su4ONR+u9tbVnnz7bnn1TDOLi6N5+Ph3de5qP8o9v3upcDHbe5S5302wrv93digeDPDlK4yKdZjtrd290N9Isv9vdKqfYH8fH/SyeJOXnd7q3v3jw8MtHOw+yURpn8c7D6WBapMNZ/kn3VjKOZ+p1EufDpxe/eK+7+d/Y/IPujePyu/LDdzpvPjp5vd35sHszHh3F2TCZJFlRfvFqu/vj9qnzJB96MpTO7qkzGk72nd0n8XiW9JzF67OeGsSEZx8TyMA6KPAju6XSEGBJetAgO1zImG+3xKLQOkgCKyAjDszmM7slX3rMOsiTLrcPcpkL/CdgwUMu7NPJS0KgyA/nI0L7HxIssK9k6NvdJmRoJxORsM/GPM8e3r4EQinkkX02l9ujW8oQyDgPiBIRAeFdDrJ7jkfAbKEPLGXA7SlQLrd9Oi6QQuEKu6HQt68SC7h9lZgv7RFX1lMkLF37MvHItYecYEAMlDuBMZ3K6rp6aveb69rzhHlAonAGTMdchpSKyB4nggHVS/pA8Wah/S9xFgG7Dg+AlPO8xrU8O7nT2exuDvMkLpKR0hydX//+84eXP7/ZOHm9V4qMTh5nz9Ps61n53U973Vd7X506+9M0K/rFtIjHzm4gek6RxJP+8+TY2b3Iu56THJWypK+Hzpzd8lfxeJwquTL/jPk9J34R56P5J175s3E6mb8Xbs+5EGp9k8CY+3ye88nPRdlgPC3nPziMx3NDnJ897jkKpZy2fDGdPk+T/mCaHZZfume9KhOrMunsviYohkK5Cyhuh/IJlNZbEJRXhXIrUNwC5fkoFFtAiSqUR6C8kHhKFcZ2UFVPWaFCEIqFCyhp95QkUFr0QlDS5ilmgZJoTrFoAeXZPSU94imlddpBVT1lhfJQKH8B5QOeIsVPS2oIyuYoW50QaPQFC6QA8BMpE0pvQ0Ri5dhDS5+ZUKHdTcKvMunN83qgBFr6mFhARW2gtEiDoNwqFKtSXRmUkVBqEisVySgtYRAqvuomJeDSZ2xSDNATghMoJboRqJVLn5p76fBjgJ6gUPq6CIo/UvyqVFcGZYYf0RM1UKT66csdBCoiOSWWhEKrn7HxMkBO8IgwqbsYhIkUv2WjT829fEoROYFA6TsYKPqsheLKoIytlwFyosZT15VROJNZJoiegBylbnhaZdT/xuQZTICe4EGVSR/rEaZwVaYAZZIGEyAnKJO+REeYiJoIl2NiKJNR+DjREqyGiUgkfQuPMAWr1ghYyhp+4kRLUH2uwKuFzwNl38qFzwWhDHnOASlBmfS9bKvYWzKfGIpklAhOhERN7DESe/rhRjt5vqSfGKrODXXEASXByBle34u28tOySPAJ3nQUICQok75/v5bYg5nMmz5ARzByiFLPnhAkcnu5rJvQI5ShjDigIhg9QUWgNFo58uCzhnHJzAEVUcOknlq+vUyAiqBM6sHgW4skgBsJRjcn9UScMC2Mkl28ZnugSl89GruOhUJFsSG2BLCHkzKqWz4aVgm53afyLfKabJI9DLGpHpQ32ETutslxQHVfXIczJehMQ2QKYAMhIa9bihoWCSjhxKbqQGowCVTQmr/Z7EugghGbuk3ocpsSKCHEpmwil8CNIrGoe1kabAIZTB2kWl8abAL3aZRc9a402ARUaA27rMm2hU1ABVKbqlelwWabJNJdKw022ySR7k1psNkmi3SXSoPNNlmkW1Eut+m1yaKg5ti7sNgmi3TrSYPNNlmkO1UabLbJIt3Y0mCzVRapPpgGm22ySHXENJhsk0S6N6bBZk0SPT5vcjncH82bXH757feXf/zz18b367VtvYP7/wLcN7ZC
    """
    expected_result = District(
        key=ndb.Key("District", "2020in", project="tbatv-prod-hrd"),
        abbreviation="in",
        advancement=json.loads(
            '{"frc5484":{"dcmp":false,"cmp":false},"frc135":{"dcmp":false,"cmp":false},"frc1747":{"dcmp":false,"cmp":false},"frc7695":{"dcmp":false,"cmp":false},"frc7477":{"dcmp":false,"cmp":false},"frc7457":{"dcmp":false,"cmp":false},"frc7454":{"dcmp":false,"cmp":false},"frc8116":{"dcmp":false,"cmp":false},"frc7198":{"dcmp":false,"cmp":false},"frc447":{"dcmp":false,"cmp":false},"frc4926":{"dcmp":false,"cmp":false},"frc7617":{"dcmp":false,"cmp":false},"frc6451":{"dcmp":false,"cmp":false},"frc5402":{"dcmp":false,"cmp":false},"frc5010":{"dcmp":false,"cmp":false},"frc7657":{"dcmp":false,"cmp":false},"frc8232":{"dcmp":false,"cmp":false},"frc45":{"dcmp":false,"cmp":true},"frc4580":{"dcmp":false,"cmp":false},"frc3176":{"dcmp":false,"cmp":false},"frc868":{"dcmp":false,"cmp":false},"frc3487":{"dcmp":false,"cmp":false},"frc3936":{"dcmp":false,"cmp":false},"frc1555":{"dcmp":false,"cmp":false},"frc6498":{"dcmp":false,"cmp":false},"frc829":{"dcmp":false,"cmp":false},"frc1024":{"dcmp":false,"cmp":false},"frc4485":{"dcmp":false,"cmp":false},"frc7502":{"dcmp":false,"cmp":false},"frc3947":{"dcmp":false,"cmp":false},"frc3940":{"dcmp":false,"cmp":false},"frc292":{"dcmp":false,"cmp":false},"frc3865":{"dcmp":false,"cmp":false},"frc6721":{"dcmp":false,"cmp":false},"frc4982":{"dcmp":false,"cmp":false},"frc234":{"dcmp":false,"cmp":false},"frc8103":{"dcmp":false,"cmp":false},"frc2867":{"dcmp":false,"cmp":false},"frc1720":{"dcmp":false,"cmp":false},"frc1646":{"dcmp":false,"cmp":false},"frc6956":{"dcmp":false,"cmp":false},"frc1501":{"dcmp":false,"cmp":false},"frc2909":{"dcmp":false,"cmp":false},"frc3147":{"dcmp":false,"cmp":false},"frc1741":{"dcmp":true,"cmp":false},"frc71":{"dcmp":false,"cmp":false},"frc4008":{"dcmp":false,"cmp":false},"frc1529":{"dcmp":false,"cmp":false},"frc2171":{"dcmp":false,"cmp":false},"frc1018":{"dcmp":false,"cmp":false},"frc3494":{"dcmp":false,"cmp":false},"frc3180":{"dcmp":false,"cmp":false},"frc461":{"dcmp":false,"cmp":false},"frc5188":{"dcmp":false,"cmp":false},"frc2197":{"dcmp":false,"cmp":false},"frc4272":{"dcmp":false,"cmp":false},"frc3559":{"dcmp":false,"cmp":false}}'
        ),
        created=datetime.datetime(2019, 9, 4, 22, 44, 13, 832001),
        display_name="FIRST Indiana Robotics",
        elasticsearch_name="Indiana",
        rankings=json.loads(
            '[{"point_total":73,"team_key":"frc234","event_points":[{"alliance_points":16,"award_points":5,"elim_points":30,"district_cmp":false,"total":73,"event_key":"2020inblo","qual_points":22}],"rank":1,"rookie_bonus":0},{"point_total":71,"team_key":"frc1720","event_points":[{"alliance_points":16,"award_points":5,"elim_points":30,"district_cmp":false,"total":71,"event_key":"2020inblo","qual_points":20}],"rank":2,"rookie_bonus":0},{"point_total":61,"team_key":"frc7457","event_points":[{"alliance_points":15,"award_points":0,"elim_points":20,"district_cmp":false,"total":56,"event_key":"2020inblo","qual_points":21}],"rank":3,"rookie_bonus":5},{"point_total":58,"team_key":"frc1501","event_points":[{"alliance_points":15,"award_points":5,"elim_points":20,"district_cmp":false,"total":58,"event_key":"2020inblo","qual_points":18}],"rank":4,"rookie_bonus":0},{"point_total":48,"team_key":"frc7454","event_points":[{"alliance_points":14,"award_points":0,"elim_points":10,"district_cmp":false,"total":43,"event_key":"2020inblo","qual_points":19}],"rank":5,"rookie_bonus":5},{"point_total":45,"team_key":"frc1024","event_points":[{"alliance_points":14,"award_points":5,"elim_points":10,"district_cmp":false,"total":45,"event_key":"2020inblo","qual_points":16}],"rank":6,"rookie_bonus":0},{"point_total":43,"team_key":"frc7657","event_points":[{"alliance_points":1,"award_points":0,"elim_points":30,"district_cmp":false,"total":38,"event_key":"2020inblo","qual_points":7}],"rank":7,"rookie_bonus":5},{"point_total":41,"team_key":"frc868","event_points":[{"alliance_points":13,"award_points":0,"elim_points":10,"district_cmp":false,"total":41,"event_key":"2020inblo","qual_points":18}],"rank":8,"rookie_bonus":0},{"point_total":36,"team_key":"frc4272","event_points":[{"alliance_points":13,"award_points":0,"elim_points":10,"district_cmp":false,"total":36,"event_key":"2020inblo","qual_points":13}],"rank":9,"rookie_bonus":0},{"point_total":36,"team_key":"frc1741","event_points":[{"alliance_points":10,"award_points":10,"elim_points":0,"district_cmp":false,"total":36,"event_key":"2020inblo","qual_points":16}],"rank":10,"rookie_bonus":0},{"point_total":33,"team_key":"frc3559","event_points":[{"alliance_points":2,"award_points":0,"elim_points":20,"district_cmp":false,"total":33,"event_key":"2020inblo","qual_points":11}],"rank":11,"rookie_bonus":0},{"point_total":32,"team_key":"frc3147","event_points":[{"alliance_points":4,"award_points":5,"elim_points":10,"district_cmp":false,"total":32,"event_key":"2020inblo","qual_points":13}],"rank":12,"rookie_bonus":0},{"point_total":32,"team_key":"frc1747","event_points":[{"alliance_points":11,"award_points":5,"elim_points":0,"district_cmp":false,"total":32,"event_key":"2020inblo","qual_points":16}],"rank":13,"rookie_bonus":0},{"point_total":31,"team_key":"frc4926","event_points":[{"alliance_points":9,"award_points":13,"elim_points":0,"district_cmp":false,"total":31,"event_key":"2020inblo","qual_points":9}],"rank":14,"rookie_bonus":0},{"point_total":29,"team_key":"frc4580","event_points":[{"alliance_points":3,"award_points":5,"elim_points":10,"district_cmp":false,"total":29,"event_key":"2020inblo","qual_points":11}],"rank":15,"rookie_bonus":0},{"point_total":29,"team_key":"frc6498","event_points":[{"alliance_points":12,"award_points":0,"elim_points":0,"district_cmp":false,"total":29,"event_key":"2020inblo","qual_points":17}],"rank":16,"rookie_bonus":0},{"point_total":29,"team_key":"frc447","event_points":[{"alliance_points":11,"award_points":5,"elim_points":0,"district_cmp":false,"total":29,"event_key":"2020inblo","qual_points":13}],"rank":17,"rookie_bonus":0},{"point_total":29,"team_key":"frc6721","event_points":[{"alliance_points":9,"award_points":5,"elim_points":0,"district_cmp":false,"total":29,"event_key":"2020inblo","qual_points":15}],"rank":18,"rookie_bonus":0},{"point_total":27,"team_key":"frc5188","event_points":[{"alliance_points":8,"award_points":5,"elim_points":0,"district_cmp":false,"total":27,"event_key":"2020inblo","qual_points":14}],"rank":19,"rookie_bonus":0},{"point_total":27,"team_key":"frc8116","event_points":[{"alliance_points":0,"award_points":8,"elim_points":0,"district_cmp":false,"total":17,"event_key":"2020inblo","qual_points":9}],"rank":20,"rookie_bonus":10},{"point_total":26,"team_key":"frc7617","event_points":[{"alliance_points":7,"award_points":0,"elim_points":0,"district_cmp":false,"total":21,"event_key":"2020inblo","qual_points":14}],"rank":21,"rookie_bonus":5},{"point_total":20,"team_key":"frc6451","event_points":[{"alliance_points":12,"award_points":0,"elim_points":0,"district_cmp":false,"total":20,"event_key":"2020inblo","qual_points":8}],"rank":22,"rookie_bonus":0},{"point_total":20,"team_key":"frc8103","event_points":[{"alliance_points":0,"award_points":5,"elim_points":0,"district_cmp":false,"total":10,"event_key":"2020inblo","qual_points":5}],"rank":23,"rookie_bonus":10},{"point_total":16,"team_key":"frc3176","event_points":[{"alliance_points":10,"award_points":0,"elim_points":0,"district_cmp":false,"total":16,"event_key":"2020inblo","qual_points":6}],"rank":24,"rookie_bonus":0},{"point_total":15,"team_key":"frc3180","event_points":[{"alliance_points":0,"award_points":0,"elim_points":0,"district_cmp":false,"total":15,"event_key":"2020inblo","qual_points":15}],"rank":25,"rookie_bonus":0},{"point_total":15,"team_key":"frc6956","event_points":[{"alliance_points":0,"award_points":5,"elim_points":0,"district_cmp":false,"total":15,"event_key":"2020inblo","qual_points":10}],"rank":26,"rookie_bonus":0},{"point_total":13,"team_key":"frc829","event_points":[{"alliance_points":6,"award_points":0,"elim_points":0,"district_cmp":false,"total":13,"event_key":"2020inblo","qual_points":7}],"rank":27,"rookie_bonus":0},{"point_total":12,"team_key":"frc3947","event_points":[{"alliance_points":0,"award_points":0,"elim_points":0,"district_cmp":false,"total":12,"event_key":"2020inblo","qual_points":12}],"rank":28,"rookie_bonus":0},{"point_total":12,"team_key":"frc3487","event_points":[{"alliance_points":0,"award_points":0,"elim_points":0,"district_cmp":false,"total":12,"event_key":"2020inblo","qual_points":12}],"rank":29,"rookie_bonus":0},{"point_total":12,"team_key":"frc292","event_points":[{"alliance_points":0,"award_points":0,"elim_points":0,"district_cmp":false,"total":12,"event_key":"2020inblo","qual_points":12}],"rank":30,"rookie_bonus":0},{"point_total":10,"team_key":"frc8232","event_points":[],"rank":31,"rookie_bonus":10},{"point_total":9,"team_key":"frc4008","event_points":[{"alliance_points":0,"award_points":0,"elim_points":0,"district_cmp":false,"total":9,"event_key":"2020inblo","qual_points":9}],"rank":32,"rookie_bonus":0},{"point_total":5,"team_key":"frc7477","event_points":[],"rank":33,"rookie_bonus":5},{"point_total":5,"team_key":"frc7695","event_points":[],"rank":34,"rookie_bonus":5},{"point_total":5,"team_key":"frc7502","event_points":[],"rank":35,"rookie_bonus":5},{"point_total":4,"team_key":"frc5010","event_points":[{"alliance_points":0,"award_points":0,"elim_points":0,"district_cmp":false,"total":4,"event_key":"2020inblo","qual_points":4}],"rank":36,"rookie_bonus":0},{"point_total":0,"team_key":"frc5484","event_points":[],"rank":37,"rookie_bonus":0},{"point_total":0,"team_key":"frc135","event_points":[],"rank":38,"rookie_bonus":0},{"point_total":0,"team_key":"frc5402","event_points":[],"rank":39,"rookie_bonus":0},{"point_total":0,"team_key":"frc7198","event_points":[],"rank":40,"rookie_bonus":0},{"point_total":0,"team_key":"frc45","event_points":[],"rank":41,"rookie_bonus":0},{"point_total":0,"team_key":"frc3936","event_points":[],"rank":42,"rookie_bonus":0},{"point_total":0,"team_key":"frc1555","event_points":[],"rank":43,"rookie_bonus":0},{"point_total":0,"team_key":"frc4485","event_points":[],"rank":44,"rookie_bonus":0},{"point_total":0,"team_key":"frc3940","event_points":[],"rank":45,"rookie_bonus":0},{"point_total":0,"team_key":"frc3865","event_points":[],"rank":46,"rookie_bonus":0},{"point_total":0,"team_key":"frc4982","event_points":[],"rank":47,"rookie_bonus":0},{"point_total":0,"team_key":"frc2867","event_points":[],"rank":48,"rookie_bonus":0},{"point_total":0,"team_key":"frc1646","event_points":[],"rank":49,"rookie_bonus":0},{"point_total":0,"team_key":"frc2909","event_points":[],"rank":50,"rookie_bonus":0},{"point_total":0,"team_key":"frc71","event_points":[],"rank":51,"rookie_bonus":0},{"point_total":0,"team_key":"frc1529","event_points":[],"rank":52,"rookie_bonus":0},{"point_total":0,"team_key":"frc2171","event_points":[],"rank":53,"rookie_bonus":0},{"point_total":0,"team_key":"frc1018","event_points":[],"rank":54,"rookie_bonus":0},{"point_total":0,"team_key":"frc3494","event_points":[],"rank":55,"rookie_bonus":0},{"point_total":0,"team_key":"frc461","event_points":[],"rank":56,"rookie_bonus":0},{"point_total":0,"team_key":"frc2197","event_points":[],"rank":57,"rookie_bonus":0}]'
        ),
        updated=datetime.datetime(2020, 12, 31, 17, 59, 52, 185404),
        year=2020,
    )
    _run_test(py2_b64, expected_result)


def test_cached_result_team_awards() -> None:
    py2_b64 = b"""
eJzNlL1v00AYxmM3H06hChAk0AlVJlXbtKKRnZgWMREB/QNar8hy7INc6o/kfAlKEAg6lgFG+C8YmBgQIysqEsxsMDEDQry2m6gkDjQOlVhs6b173ufu3p+eh/ytFlc0bNfEllfS7+rUnK0G3xa/8qg1o87xiUSj2DjlPWA1nXXWmtQ11+rUpGdPnEkFOwvZsiRVbKLJ0kl6DuWCJhrrNrGGnbYtJlZ5YZaeFzIoY1CsM2xCKSu8ffzi3Zfvr3gqoxTuYIdBdckYNfJ6qZv+8h6XDn2Y6bsEkiGXBK2iPMUGaRJ/seG5jmYRj4ncahEt3SsEJ8O4cFV02pZ1SSwwrNsaqGuYQlGWFen+lC0kCVpcRtmgfCCMvlVShS17XOY2NXxjuNXEMjADWfCy7aY5eNmX/ZedQ8ku1ikUZ4T9XK8k5JDg6DbWPOYX59GFLdfdIVisWpa4zWBnMFBxkxJT7+5ykSOu1X0wkmrPB2M5Aoz8QCWASjGZVh7LBT/KxaefT95MzgXYHB8XZXn9n3AxXQtF2YiBFpw9PloTy+CMUUR+7M/0MJHvc72FISLz6PQWvkNcR7fETQJf8N3looAKKUypz7gjxZMvqoyPp/lRDF8/f/q/YRgvW8aFRP9+QyOpDI1kAV28oRPbwvR6nXY9+It+c3G7SShhYWAMJ8XBa4czSqudoyXFBrEmS4of+1+/fZ54RGBzzCO6Nq7FMlr8a4t15cqUHeLlRIiJ8rts8U+yNMjgtDFUY1JiMM/DSH6IlxIhTDVc+gXAAdEx
    """
    expected_result = [
        Award(
            key=ndb.Key("Award", "2003mi_10", project="tbatv-prod-hrd"),
            award_type_enum=10,
            created=datetime.datetime(2013, 11, 23, 21, 17, 57, 121480),
            event=ndb.Key("Event", "2003mi", project="tbatv-prod-hrd"),
            event_type_enum=0,
            name_str="Rookie All Star Award Friday",
            recipient_json_list=['{"awardee": null, "team_number": 1000}'],
            team_list=[ndb.Key("Team", "frc1000", project="tbatv-prod-hrd")],
            updated=datetime.datetime(2013, 11, 23, 21, 17, 57, 121460),
            year=2003,
        ),
        Award(
            key=ndb.Key("Award", "2004dt_2", project="tbatv-prod-hrd"),
            award_type_enum=2,
            created=datetime.datetime(2013, 11, 23, 21, 17, 20, 943970),
            event=ndb.Key("Event", "2004dt", project="tbatv-prod-hrd"),
            event_type_enum=0,
            name_str="Regional Finalist",
            recipient_json_list=['{"awardee": null, "team_number": 1447}'],
            team_list=[ndb.Key("Team", "frc1447", project="tbatv-prod-hrd")],
            updated=datetime.datetime(2013, 11, 23, 21, 17, 20, 943960),
            year=2004,
        ),
        Award(
            key=ndb.Key("Award", "2004dt_30", project="tbatv-prod-hrd"),
            award_type_enum=30,
            created=datetime.datetime(2013, 11, 23, 21, 17, 20, 947390),
            event=ndb.Key("Event", "2004dt", project="tbatv-prod-hrd"),
            event_type_enum=0,
            name_str="DaimlerChrysler Team Spirit Award",
            recipient_json_list=['{"awardee": null, "team_number": 1000}'],
            team_list=[ndb.Key("Team", "frc1000", project="tbatv-prod-hrd")],
            updated=datetime.datetime(2013, 11, 23, 21, 17, 20, 947380),
            year=2004,
        ),
        Award(
            key=ndb.Key("Award", "2007il_2", project="tbatv-prod-hrd"),
            award_type_enum=2,
            created=datetime.datetime(2013, 11, 23, 21, 14, 55, 727100),
            event=ndb.Key("Event", "2007il", project="tbatv-prod-hrd"),
            event_type_enum=0,
            name_str="Regional Finalist",
            recipient_json_list=['{"awardee": null, "team_number": 447}'],
            team_list=[
                ndb.Key("Team", "frc447", project="tbatv-prod-hrd"),
            ],
            updated=datetime.datetime(2013, 11, 23, 21, 14, 55, 727100),
            year=2007,
        ),
    ]
    _run_test(py2_b64, expected_result)
