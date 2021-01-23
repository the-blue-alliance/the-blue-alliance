import base64
import datetime
import io
import json
import pickle
import unittest2
import zlib

from google.appengine.api.datastore_types import GeoPt
from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models.award import Award
from models.cached_query_result import ImportFixingPickleProperty
from models.event import Event
from models.location import Location
from models.media import Media

"""
This is a test that makes sure the legacy app can read models
pickled by the py3 app. This is important for CachedQueryResult
compatibility between the two versions
"""


class ModelWithInt(ndb.Model):
    int_prop = ndb.IntegerProperty()


class ModelWithIntRepeated(ndb.Model):
    int_prop = ndb.IntegerProperty(repeated=True)


class ModelWithString(ndb.Model):
    str_prop = ndb.StringProperty()


class ModelWithKey(ndb.Model):
    key_prop = ndb.KeyProperty()


class TestCachedQueryResultCompatibility(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()

    def tearDown(self):
        self.testbed.deactivate()

    def test_round_trip_model_pickle_integer(self):
        ModelWithInt(
            id="test_model",
            int_prop=2018,
        ).put()
        model = ModelWithInt.get_by_id("test_model")

        pickled = pickle.dumps(model, protocol=2)
        check = pickle.loads(pickled)

        self.assertEqual(check, model)

    def test_round_trip_model_pickle_integer_repeated(self):
        ModelWithIntRepeated(
            id="test_model",
            int_prop=[2018, 2019, 2020],
        ).put()
        model = ModelWithIntRepeated.get_by_id("test_model")

        pickled = pickle.dumps(model, protocol=2)
        check = pickle.loads(pickled)

        self.assertEqual(check, model)

    def test_round_trip_model_pickle_key(self):
        ModelWithKey(
            id="test_model",
            key_prop=ndb.Key(Media, "test_media"),
        ).put()
        model = ModelWithKey.get_by_id("test_model")

        pickled = pickle.dumps(model, protocol=2)
        check = pickle.loads(pickled)

        self.assertEqual(check, model)

    def test_round_trip_model_pickle_string(self):
        ModelWithString(
            id="test_model",
            str_prop="abc123",
        ).put()
        model = ModelWithString.get_by_id("test_model")

        pickled = pickle.dumps(model, protocol=2)
        check = pickle.loads(pickled)

        self.assertEqual(check, model)

    def test_cached_result_team_year_media(self):
        py3_b64 = "eJxlj7FKA0EQhvdikjsvQSEElK2CBMRATpQU2gg+gI1YpJFjszsXN7ndu53bBGKlFoI+gY2lhUVaH+DyYt7FQjTNMMz/z//zPVRuDeEjxqegRcATpRIdqERAnAUKhGT+1Xoa5+jRVHjIC4lnPuhy8c3W8MIhZHI52bEjZuf9FBPRv0OBx41Wbf150JU6s2yMTJVqJGMIrbRMy5mycgyYDc5Oz5u477nU5QjMguiQ3raXv62+8pf8M1+u3lfLCrZoU4BlMs7CSZbowkPw0NuljShBkGMdTmFRHNu0tRmPe3R3TRPaRQoh6JkqrBXPRUrbKcp50RpupA+ojxABFrCQdZxel//HzO6rN8BU/uq4EfKyyYofklkqfkk+/pL4tLoAhmVH/uQQUx3WCSExs1KfmNqzqV8bd8SCb5mBiUo="

        expected_result = [
            Media(
                key=ndb.Key(
                    "Media",
                    "instagram-profile_titaniumtigers4829",
                    app="tbatv-prod-hrd",
                ),
                created=datetime.datetime(2020, 12, 20, 20, 3, 17, 962520),
                details_json=None,
                foreign_key=u"titaniumtigers4829",
                media_type_enum=7,
                private_details_json=None,
                references=[ndb.Key("Team", "frc4829", app="tbatv-prod-hrd")],
                updated=datetime.datetime(2020, 12, 20, 20, 3, 17, 962533),
                year=None,
            )
        ]

        value = ImportFixingPickleProperty()._from_base_type(
            zlib.decompress(base64.b64decode(py3_b64))
        )
        self.assertEqual(value, expected_result)

    def test_cached_query_result_team_awards(self):
        py3_b64 = "eJzFlEtv00AUhR3n5aSP0AYJZKHKpLSUigbnoRaxK4X+gJRFNsia2AOZ1I94PGkVEFJhgRAseBQJ2LKDVResCurC/mNc26iS06Q0Cagb25qZc+/4nk9nj39oc0tqA6nb2NSKqmUYllk0LA3rThHtIqpl14OnHbvx3OZVRYUt1cli0//I2vG6wHNca7E1zRqI7ay0qaWtNKlGL07MJgNlIVOW5YpBlJI8SS+JuaCowrptrGCzY0jcMi9k6WUhLaZVihHDGixlBO+V+8Y98N57372f7iFPb4lJvINNBpvX1N5uzpPkfX/TfR1Lhd2Y5vcKFD29OFoUcqJgIgMrDqOwNideqVnWNsHSuq5LWwxRKbi5tEmJhrp0A87nKVZJm/jlWo5lKjpxmBRbXhIXnxaCP8K4cEcyO7p+UyowjAwF+jUwhcVSqSo/G7uILEORipgJlv8I+w0i8QAOwBzSj6jqd4ZBDKuCVqAKHOm0tWNH3B9RR6bERBcjf4BxwdvPuS9inJ2opziO0xEjZslOvrRTNTvdaProCM14fddHZeEEKvljVAQwr6oxpTyQFL4PKV+9I/ettzcKKdDsNFLme0jJizM1/JhYJtKlTQJPmOjYzpZLq/8Ij3GLVKtrwzMG1x+ZsWFVcMF+ZHqfowREyPwYkplpAo7Zmj0R4jgJOH6InSG5fBwrg5Nr7iSP7pH7xX33X3is9PA4L169h4ihY7rRpF0H3pI/LmmrTShhYYqdT/IMzpDIbPo5NeU7NV2zc6FTF8Ap5yzBsUb0IYPjl7fvHXiH3rfhjYJm5x4cgTF3Bxe5Li78tchq9fbYNUaKjRCQclQ1f4oqBSq47fCiQaHR434ExU8hijM+irM1O9/Axd8QcvqT"

        expected_result = [
            Award(
                key=ndb.Key("Award", "2003mi_10", app="tbatv-prod-hrd"),
                award_type_enum=10,
                created=datetime.datetime(2013, 11, 23, 21, 17, 57, 121480),
                event=ndb.Key("Event", "2003mi", app="tbatv-prod-hrd"),
                event_type_enum=0,
                name_str=u"Rookie All Star Award Friday",
                recipient_json_list=[
                    u'{"awardee": null, "team_number": 1140}',
                    u'{"awardee": null, "team_number": 1000}',
                ],
                team_list=[
                    ndb.Key("Team", "frc1140", app="tbatv-prod-hrd"),
                    ndb.Key("Team", "frc1000", app="tbatv-prod-hrd"),
                ],
                updated=datetime.datetime(2013, 11, 23, 21, 17, 57, 121460),
                year=2003,
            ),
            Award(
                key=ndb.Key("Award", "2004dt_2", app="tbatv-prod-hrd"),
                award_type_enum=2,
                created=datetime.datetime(2013, 11, 23, 21, 17, 20, 943970),
                event=ndb.Key("Event", "2004dt", app="tbatv-prod-hrd"),
                event_type_enum=0,
                name_str=u"Regional Finalist",
                recipient_json_list=[
                    u'{"awardee": null, "team_number": 1216}',
                    u'{"awardee": null, "team_number": 1000}',
                    u'{"awardee": null, "team_number": 1447}',
                ],
                team_list=[
                    ndb.Key("Team", "frc1216", app="tbatv-prod-hrd"),
                    ndb.Key("Team", "frc1000", app="tbatv-prod-hrd"),
                    ndb.Key("Team", "frc1447", app="tbatv-prod-hrd"),
                ],
                updated=datetime.datetime(2013, 11, 23, 21, 17, 20, 943960),
                year=2004,
            ),
            Award(
                key=ndb.Key("Award", "2004dt_30", app="tbatv-prod-hrd"),
                award_type_enum=30,
                created=datetime.datetime(2013, 11, 23, 21, 17, 20, 947390),
                event=ndb.Key("Event", "2004dt", app="tbatv-prod-hrd"),
                event_type_enum=0,
                name_str=u"DaimlerChrysler Team Spirit Award",
                recipient_json_list=[u'{"awardee": null, "team_number": 1000}'],
                team_list=[ndb.Key("Team", "frc1000", app="tbatv-prod-hrd")],
                updated=datetime.datetime(2013, 11, 23, 21, 17, 20, 947380),
                year=2004,
            ),
            Award(
                key=ndb.Key("Award", "2007il_2", app="tbatv-prod-hrd"),
                award_type_enum=2,
                created=datetime.datetime(2013, 11, 23, 21, 14, 55, 727100),
                event=ndb.Key("Event", "2007il", app="tbatv-prod-hrd"),
                event_type_enum=0,
                name_str=u"Regional Finalist",
                recipient_json_list=[
                    u'{"awardee": null, "team_number": 1000}',
                    u'{"awardee": null, "team_number": 648}',
                    u'{"awardee": null, "team_number": 447}',
                ],
                team_list=[
                    ndb.Key("Team", "frc1000", app="tbatv-prod-hrd"),
                    ndb.Key("Team", "frc648", app="tbatv-prod-hrd"),
                    ndb.Key("Team", "frc447", app="tbatv-prod-hrd"),
                ],
                updated=datetime.datetime(2013, 11, 23, 21, 14, 55, 727100),
                year=2007,
            ),
        ]

        value = ImportFixingPickleProperty()._from_base_type(
            zlib.decompress(base64.b64decode(py3_b64))
        )
        self.assertEqual(value, expected_result)

    def test_cached_result_team_year_events(self):
        py3_b64 = "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"

    expected_result = [
        Event(
            key=ndb.Key("Event", "2020arli", app="tbatv-prod-hrd"),
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
                lat_lng=GeoPt(34.7232243, -92.2989882),
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
            key=ndb.Key("Event", "2020lake", app="tbatv-prod-hrd"),
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
                lat_lng=GeoPt(30.0395012, -90.2405773),
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
