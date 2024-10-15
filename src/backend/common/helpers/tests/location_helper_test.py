import json
import os
import unittest
from typing import Optional

import pytest
from google.appengine.ext import ndb

from backend.common.helpers.location_helper import LocationHelper
from backend.common.models.event import Event
from backend.common.models.sitevar import Sitevar
from backend.common.models.team import Team


@pytest.mark.usefixtures("ndb_context")
class TestLocationHelper(unittest.TestCase):
    test_google_api_key: Optional[str] = None

    def setUp(self):
        # Load env vars that contain test keys
        self.test_google_api_key = os.environ.get(
            "TEST_GOOGLE_API_KEY", ""
        )  # Frome in Travis CI
        if not self.test_google_api_key:
            try:
                with open("test_keys.json") as data_file:
                    test_keys = json.load(data_file)
                    self.test_google_api_key = test_keys.get("test_google_api_key", "")
            except Exception:
                # Just go without
                pass

        Sitevar(
            id="google.secrets",
            values_json=json.dumps({"api_key": self.test_google_api_key}),
        ).put()

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_generic(self, mocker):
        # 2016cama (generic event)
        event = Event(
            id="2016cama",
            year=2016,
            city="Madera",
            state_prov="CA",
            country="USA",
            postalcode="93637",
            venue="Madera South High School",
            venue_address="Madera South High School\n705 W. Pecan Avenue\nMadera, CA 93637\nUSA",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, "Madera South High School")
        self.assertEqual(
            event.normalized_location.formatted_address,
            "705 W Pecan Ave, Madera, CA 93637, USA",
        )
        self.assertEqual(event.normalized_location.street_number, "705")
        self.assertEqual(event.normalized_location.street, "West Pecan Avenue")
        self.assertEqual(event.normalized_location.city, "Madera")
        self.assertEqual(event.normalized_location.state_prov, "California")
        self.assertEqual(event.normalized_location.state_prov_short, "CA")
        self.assertEqual(event.normalized_location.country, "United States")
        self.assertEqual(event.normalized_location.country_short, "US")
        self.assertEqual(event.normalized_location.postal_code, "93637")
        self.assertEqual(
            event.normalized_location.lat_lng, ndb.GeoPt(36.9393999, -120.0664811)
        )

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_odd_address(self):
        # 2016cada (weird address)
        event = Event(
            id="2016cada",
            year=2016,
            city="Davis",
            state_prov="CA",
            country="USA",
            postalcode="95616",
            venue="UC Davis ARC Pavilion",
            venue_address="UC Davis ARC Pavilion\nCorner of Orchard and LaRue\nDavis, CA 95616\nUSA",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, "The Pavilion")
        # self.assertEqual(event.normalized_location.formatted_address, 'Davis, CA 95616, USA')
        # self.assertEqual(event.normalized_location.street_number, None)
        # self.assertEqual(event.normalized_location.street, None)
        self.assertEqual(event.normalized_location.city, "Davis")
        self.assertEqual(event.normalized_location.state_prov, "California")
        self.assertEqual(event.normalized_location.state_prov_short, "CA")
        self.assertEqual(event.normalized_location.country, "United States")
        self.assertEqual(event.normalized_location.country_short, "US")
        self.assertEqual(event.normalized_location.postal_code, "95616")
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(38.5418888, -121.7595864))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_odd_venue(self):
        # 2016casj (weird venue)
        event = Event(
            id="2016casj",
            year=2016,
            city="San Jose",
            state_prov="CA",
            country="USA",
            postalcode="95112",
            venue="San Jose State University - The Event Center",
            venue_address="San Jose State University - The Event Center\n290 South 7th Street\nSan Jose, CA 95112\nUSA",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, "The Event Center at SJSU")
        # self.assertEqual(event.normalized_location.formatted_address, '290 S 7th St, San Jose, CA 95112, USA')
        # self.assertEqual(event.normalized_location.street_number, '290')
        # self.assertEqual(event.normalized_location.street, 'South 7th Street')
        self.assertEqual(event.normalized_location.city, "San Jose")
        self.assertEqual(event.normalized_location.state_prov, "California")
        self.assertEqual(event.normalized_location.state_prov_short, "CA")
        self.assertEqual(event.normalized_location.country, "United States")
        self.assertEqual(event.normalized_location.country_short, "US")
        self.assertEqual(event.normalized_location.postal_code, "95112")
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(37.33522809999999, -121.8800817))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_no_address(self):
        # 2016cmp (no venue address)
        event = Event(
            id="2016cmp",
            year=2016,
            city="St. Louis",
            state_prov="MO",
            country="USA",
            postalcode="95112",
            venue="The Dome at America's Center",
            venue_address=None,
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, "The Dome at America's Center")
        # self.assertEqual(event.normalized_location.formatted_address, '901 N Broadway, St. Louis, MO 63101, USA')
        # self.assertEqual(event.normalized_location.street_number, '901')
        # self.assertEqual(event.normalized_location.street, 'North Broadway')
        self.assertEqual(event.normalized_location.city, "St. Louis")
        self.assertEqual(event.normalized_location.state_prov, "Missouri")
        self.assertEqual(event.normalized_location.state_prov_short, "MO")
        self.assertEqual(event.normalized_location.country, "United States")
        self.assertEqual(event.normalized_location.country_short, "US")
        self.assertEqual(event.normalized_location.postal_code, "63101")
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(38.6328287, -90.1885095))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_australia(self):
        # 2016ausy (Australia event)
        event = Event(
            id="2016ausy",
            year=2016,
            city="Sydney Olympic Park",
            state_prov="NSW",
            country="Australia",
            postalcode="2127",
            venue="Sydney Olympic Park Sports Centre",
            venue_address="Sydney Olympic Park Sports Centre\nOlympic Boulevard\nSydney Olympic Park, NSW 2127\nAustralia",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(
            event.normalized_location.name, "Sydney Olympic Park Sports Centre"
        )
        # self.assertEqual(event.normalized_location.formatted_address, 'Olympic Blvd, Sydney Olympic Park NSW 2127, Australia')
        # self.assertEqual(event.normalized_location.street_number, None)
        # self.assertEqual(event.normalized_location.street, 'Olympic Boulevard')
        self.assertEqual(event.normalized_location.city, "Sydney Olympic Park")
        self.assertEqual(event.normalized_location.state_prov, "New South Wales")
        self.assertEqual(event.normalized_location.state_prov_short, "NSW")
        self.assertEqual(event.normalized_location.country, "Australia")
        self.assertEqual(event.normalized_location.country_short, "AU")
        self.assertEqual(event.normalized_location.postal_code, "2127")
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(-33.85341090000001, 151.0693752))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_canada(self):
        # 2016abca (Canada event)
        event = Event(
            id="2016abca",
            year=2016,
            city="Calgary",
            state_prov="AB",
            country="Canada",
            postalcode="T2N 1N4",
            venue="The Olympic Oval",
            venue_address="The Olympic Oval\nUniversity of Calgary\nCalgary, AB T2N 1N4\nCanada",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, "Olympic Oval")
        # self.assertEqual(event.normalized_location.formatted_address, '2500 University Dr NW, Calgary, AB T2N 1N4, Canada')
        # self.assertEqual(event.normalized_location.street_number, '2500')
        # self.assertEqual(event.normalized_location.street, 'University Dr NW')
        self.assertEqual(event.normalized_location.city, "Calgary")
        self.assertEqual(event.normalized_location.state_prov, "Alberta")
        self.assertEqual(event.normalized_location.state_prov_short, "AB")
        self.assertEqual(event.normalized_location.country, "Canada")
        self.assertEqual(event.normalized_location.country_short, "CA")
        self.assertEqual(event.normalized_location.postal_code, "T2N 1N4")
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(51.07701139999999, -114.1357481))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_china(self):
        # 2016gush (China event with really bad location details)
        event = Event(
            id="2016gush",
            year=2016,
            city="Shenzhen City",
            state_prov="44",
            country="China",
            postalcode="518000",
            venue="The Sports Center of Shenzhen University",
            venue_address="The Sports Center of Shenzhen University\nNo. 2032 Liuxian Road\nNanshan District\nShenzhen City, 44 518000\nChina",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(
            event.normalized_location.name, "Shenzhen University Town Sports Center"
        )
        # self.assertEqual(event.normalized_location.formatted_address, 'Liuxian Ave, Nanshan Qu, Shenzhen Shi, Guangdong Sheng, China, 518055')
        # self.assertEqual(event.normalized_location.street_number, None)
        # self.assertEqual(event.normalized_location.street, 'Liuxian Avenue')
        self.assertEqual(event.normalized_location.city, "Shenzhen Shi")
        self.assertEqual(event.normalized_location.state_prov, "Guangdong Sheng")
        self.assertEqual(event.normalized_location.state_prov_short, "Guangdong Sheng")
        self.assertEqual(event.normalized_location.country, "China")
        self.assertEqual(event.normalized_location.country_short, "CN")
        self.assertEqual(event.normalized_location.postal_code, "518055")
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(22.585279, 113.978825))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_2016code(self):
        # 2016code
        event = Event(
            id="2016code",
            year=2016,
            city="Denver",
            state_prov="CO",
            country="USA",
            postalcode="80210",
            venue=" University of Denver - Daniel L. Ritchie Center",
            venue_address="University of Denver - Daniel L. Ritchie Center\n2201 East Asbury Ave\nDenver, CO 80210\nUSA",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, "Ritchie Center")
        # self.assertEqual(event.normalized_location.formatted_address, '2240 Buchtel Blvd S, Denver, CO 80210, USA')
        # self.assertEqual(event.normalized_location.street_number, '2240')
        # self.assertEqual(event.normalized_location.street, 'Buchtel Boulevard South')
        self.assertEqual(event.normalized_location.city, "Denver")
        self.assertEqual(event.normalized_location.state_prov, "Colorado")
        self.assertEqual(event.normalized_location.state_prov_short, "CO")
        self.assertEqual(event.normalized_location.country, "United States")
        self.assertEqual(event.normalized_location.country_short, "US")
        self.assertEqual(event.normalized_location.postal_code, "80210")
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(39.6819652, -104.9618983))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_2016ilpe(self):
        # 2016ilpe
        event = Event(
            id="2016ilpe",
            year=2016,
            city="Peoria",
            state_prov="IL",
            country="USA",
            postalcode="61625",
            venue="Renaissance Coliseum - Bradley University",
            venue_address="Renaissance Coliseum - Bradley University\n1600 W. Main Street\nPeoria, IL 61625\nUSA",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, "Renaissance Coliseum")
        # self.assertEqual(event.normalized_location.formatted_address, 'Renaissance Coliseum, N Maplewood Ave, Peoria, IL 61606, USA')
        # self.assertEqual(event.normalized_location.street_number, None)
        # self.assertEqual(event.normalized_location.street, 'North Maplewood Avenue')
        self.assertEqual(event.normalized_location.city, "Peoria")
        self.assertEqual(event.normalized_location.state_prov, "Illinois")
        self.assertEqual(event.normalized_location.state_prov_short, "IL")
        self.assertEqual(event.normalized_location.country, "United States")
        self.assertEqual(event.normalized_location.country_short, "US")
        self.assertEqual(event.normalized_location.postal_code, "61606")
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(40.69919369999999, -89.61780639999999))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_2017isde1(self):
        # 2017isde1
        event = Event(
            id="2016ide1",
            year=2016,
            city="Haifa",
            state_prov="HA",
            country="Israel",
            postalcode="00000",
            venue="Technion Sports Center",
            venue_address="Technion Sports Center\nTechnion\nHaifa, HA 00000\nIsrael",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, "Technion Sports Center")
        # self.assertEqual(event.normalized_location.formatted_address, 'Derech Ya\'akov Dori, Haifa, Israel')
        # self.assertEqual(event.normalized_location.street_number, None)
        # self.assertEqual(event.normalized_location.street, 'Derech Ya\'akov Dori')
        self.assertEqual(event.normalized_location.city, "Haifa")
        self.assertEqual(event.normalized_location.state_prov, "Haifa District")
        self.assertEqual(event.normalized_location.state_prov_short, "Haifa District")
        self.assertEqual(event.normalized_location.country, "Israel")
        self.assertEqual(event.normalized_location.country_short, "IL")
        self.assertEqual(event.normalized_location.postal_code, None)
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(32.77911630000001, 35.01909250000001))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_2017isde3(self):
        # 2017isde3
        event = Event(
            id="2016isde3",
            year=2016,
            city="Tel-Aviv, Yafo",
            state_prov="TA",
            country="Israel",
            postalcode="00000",
            venue="Shlomo Group Arena",
            venue_address="Shlomo Group Arena\n7 Isaac Remba St\nTel-Aviv, Yafo, TA 00000\nIsrael",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, "Shlomo Group arena")
        # self.assertEqual(event.normalized_location.formatted_address, 'Isaac Remba St 27, Tel Aviv-Yafo, Israel')
        # self.assertEqual(event.normalized_location.street_number, '27')
        # self.assertEqual(event.normalized_location.street, 'Isaac Remba Street')
        self.assertEqual(event.normalized_location.city, "Tel Aviv-Yafo")
        self.assertEqual(event.normalized_location.state_prov, "Tel Aviv District")
        self.assertEqual(
            event.normalized_location.state_prov_short, "Tel Aviv District"
        )
        self.assertEqual(event.normalized_location.country, "Israel")
        self.assertEqual(event.normalized_location.country_short, "IL")
        self.assertEqual(event.normalized_location.postal_code, None)
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(32.1090726,34.8113608))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_2016mndu(self):
        # 2017mndu
        event = Event(
            id="2016mndu",
            year=2016,
            city="Duluth",
            state_prov="MN",
            country="USA",
            postalcode="55802",
            venue="DECC Arena/South Pioneer Hall",
            venue_address="DECC Arena/South Pioneer Hall\nDuluth Entertainment Convention Center\n350 Harbor Drive\nDuluth, MN 55802\nUSA",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(
            event.normalized_location.name, "Duluth Entertainment Convention Center"
        )
        # self.assertEqual(event.normalized_location.formatted_address, '350 Harbor Dr, Duluth, MN 55802, USA')
        # self.assertEqual(event.normalized_location.street_number, '350')
        # self.assertEqual(event.normalized_location.street, 'Harbor Drive')
        self.assertEqual(event.normalized_location.city, "Duluth")
        self.assertEqual(event.normalized_location.state_prov, "Minnesota")
        self.assertEqual(event.normalized_location.state_prov_short, "MN")
        self.assertEqual(event.normalized_location.country, "United States")
        self.assertEqual(event.normalized_location.country_short, "US")
        self.assertEqual(event.normalized_location.postal_code, "55802")
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(46.78126760000001, -92.09950649999999))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_2017mxto(self):
        # 2017mxto
        event = Event(
            id="2016mxto",
            year=2016,
            city="Torreon",
            state_prov="COA",
            country="Mexico",
            postalcode="27250",
            venue="ITESM Campus Laguna - Santiago Garza de la Mora",
            venue_address="ITESM Campus Laguna - Santiago Garza de la Mora\nPaseo del Tecnologico #751\nTorreon, COA 27250\nMexico",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(
            event.normalized_location.name,
            "Instituto Tecnol\xf3gico de Estudios Superiores de Monterrey",
        )
        # self.assertEqual(event.normalized_location.formatted_address, u'Paseo del Tecnol\xf3gico 751, La Rosita, Amp la Rosita, 27250 Torre\xf3n, Coah., Mexico')
        # self.assertEqual(event.normalized_location.street_number, None)
        # self.assertEqual(event.normalized_location.street, None)
        self.assertEqual(event.normalized_location.city, "Torre\xf3n")
        self.assertEqual(event.normalized_location.state_prov, "Coahuila de Zaragoza")
        self.assertEqual(event.normalized_location.state_prov_short, "Coah.")
        self.assertEqual(event.normalized_location.country, "Mexico")
        self.assertEqual(event.normalized_location.country_short, "MX")
        self.assertEqual(event.normalized_location.postal_code, "27250")
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(25.5173546, -103.3976534))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_nonsense(self):
        # 2017micmp (Nonsense data)
        event = Event(
            id="2017micmp",
            year=2017,
            city="TBD",
            state_prov="Mi",
            country="USA",
            postalcode="00000",
            venue="TBD - See Site Information",
            venue_address="TBD - See Site Information\nTBD\nTBD, MI 00000\nUSA",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, None)
        # self.assertEqual(event.normalized_location.formatted_address, None)
        # self.assertEqual(event.normalized_location.street_number, None)
        # self.assertEqual(event.normalized_location.street, None)
        self.assertEqual(event.normalized_location.city, None)
        self.assertEqual(event.normalized_location.state_prov, None)
        self.assertEqual(event.normalized_location.state_prov_short, None)
        self.assertEqual(event.normalized_location.country, None)
        self.assertEqual(event.normalized_location.country_short, None)
        self.assertEqual(event.normalized_location.postal_code, None)
        # self.assertEqual(event.normalized_location.lat_lng, None)

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_event_location_2008cal(self):
        # 2008cal (Only has city, state, country)
        event = Event(
            id="2008cal",
            year=2008,
            city="San Jose",
            state_prov="CA",
            country="USA",
        )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, None)
        # self.assertEqual(event.normalized_location.formatted_address, 'San Jose, CA, USA')
        # self.assertEqual(event.normalized_location.street_number, None)
        # self.assertEqual(event.normalized_location.street, None)
        self.assertEqual(event.normalized_location.city, "San Jose")
        self.assertEqual(event.normalized_location.state_prov, "California")
        self.assertEqual(event.normalized_location.state_prov_short, "CA")
        self.assertEqual(event.normalized_location.country, "United States")
        self.assertEqual(event.normalized_location.country_short, "US")
        self.assertEqual(event.normalized_location.postal_code, None)
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(37.3382082, -121.8863286))