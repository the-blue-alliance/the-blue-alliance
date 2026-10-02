import json
import logging
import os
import unittest
from typing import Any, cast, Dict, List, Optional
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
import requests
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from requests_mock import Mocker

from backend.common.helpers.location_helper import (
    LatLng,
    LocationHelper,
    LocationInfo,
)
from backend.common.models.event import Event
from backend.common.models.location import Location
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

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_604(self):
        # Team 604 (generic team)
        team = Team(
            id="frc604",
            name="Brin Wojcicki Foundation/IBM/Google.org/Qualcomm/Apple/Team Grandma/BAE Systems/Western Digital/WAGIC/Lockheed Martin/TE connectivity/Leland Bridge/Intuitive Surgical/San Jose City Councilman J. Khamis/eBay/Cisco/Dell/MDR Precision/ Benevity /SOLIDWORKS/Sierra Radio Systems/HSC Electronic Supply/Hurricane Electric/Dropbox/STL Shipping by FRC3256/GitHub & Leland High",
            city="San Jose",
            state_prov="California",
            postalcode="95120",
            country="USA",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, 'Leland High School')
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, '6677 Camden Avenue, San Jose, CA 95120, USA')
        # self.assertEqual(team.normalized_location.street_number, '6677')
        # self.assertEqual(team.normalized_location.street, 'Camden Avenue')
        self.assertEqual(team.normalized_location.city, "San Jose")
        self.assertEqual(team.normalized_location.state_prov, "California")
        self.assertEqual(team.normalized_location.state_prov_short, "CA")
        self.assertEqual(team.normalized_location.country, "United States")
        self.assertEqual(team.normalized_location.country_short, "US")
        self.assertEqual(team.normalized_location.postal_code, "95120")
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(37.217065, -121.842901))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_456(self):
        # Team 456 (Many schools, odd school ordering)
        team = Team(
            id="frc456",
            name="US Army Engineer Research & Development Center / Vicksburg-Warren School District / National Defense Education Program / NASA / Diane and Donald Cargile / Ginny and Chuck Dickerson & Warren Central High School & Vicksburg Catholic School & Vicksburg High School & Home School",
            city="Vicksburg",
            state_prov="Mississippi",
            postalcode="39180",
            country="USA",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, None)
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, 'Vicksburg, MS, USA')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, "Vicksburg")
        self.assertEqual(team.normalized_location.state_prov, "Mississippi")
        self.assertEqual(team.normalized_location.state_prov_short, "MS")
        self.assertEqual(team.normalized_location.country, "United States")
        self.assertEqual(team.normalized_location.country_short, "US")
        # self.assertEqual(team.normalized_location.postal_code, '39180')
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(32.3526456, -90.877882))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_1868(self):
        # Team 1868 (Odd Sponsors, multiple schools)
        team = Team(
            id="frc1868",
            name="NASA Ames Research Center / St. Jude Medical Foundation / Google / Nvidia / Brin Worcicki Foundation / Qualcomm / Intuitive Surgical / Motorola / World Metal Finishing / Applied Welding / Weiss Enterprises / Solidworks / Wildbit / Fiber Internet Center & Girl Scout Troop 62868",
            city="Mountain View",
            state_prov="California",
            postalcode="94035",
            country="USA",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, None)
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, 'Mountain View, CA 94035, USA')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, "Mountain View")
        self.assertEqual(team.normalized_location.state_prov, "California")
        self.assertEqual(team.normalized_location.state_prov_short, "CA")
        self.assertEqual(team.normalized_location.country, "United States")
        self.assertEqual(team.normalized_location.country_short, "US")
        self.assertEqual(team.normalized_location.postal_code, "94035")
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(37.41752, -122.0525))
        # Disabled until we can get more accurate
        # self.assertEqual(team.normalized_location.name, 'NASA Ames Research Center')
        # self.assertEqual(team.normalized_location.formatted_address, 'MOFFETT FIELD, CA 94035, USA')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        # self.assertEqual(team.normalized_location.city, 'MOFFETT FIELD')
        # self.assertEqual(team.normalized_location.state_prov, 'California')
        # self.assertEqual(team.normalized_location.state_prov_short, 'CA')
        # self.assertEqual(team.normalized_location.country, 'United States')
        # self.assertEqual(team.normalized_location.country_short, 'US')
        # self.assertEqual(team.normalized_location.postal_code, '94035')
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(37.4090697, -122.0638253))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_3504(self):
        # Team 3504 (Odd Sponsors, multiple schools)
        team = Team(
            id="frc3504",
            name="Field Robotics Center, Carnegie Mellon University / American Eagle Outfitters & Fox Chapel Area Hs & Oakland Catholic High School & Pittsburgh Brashear Hs & Pittsburgh Science and Technology Academy 6-12 & Avonworth Hs & Pittsburgh Capa 6-12 & Bishop Canevin High School & Dorseyville Ms & Plum Shs & Winchester Thurston School & North Allegheny Shs & North Allegheny Ihs & Pine-Richland Hs & Seneca Valley Shs & Upper Saint Clair Hs & The Ellis School & PA Cyber Charter School & Aquinas Academy & Penn Hills Shs & Harrold Middle School & Sacred Heart Elementary School & Pittsburgh Obama 6-12 & Hampton Middle School & Hampton Hs & Franklin Regional Ms & Canon-Mcmillan Shs & South Fayette Ms & Community College Allegheny County & Home School & Home School & Home School",
            city="Pittsburgh",
            state_prov="Pennsylvania",
            postalcode="15213",
            country="USA",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, None)
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, 'Pittsburgh, PA 15213, USA')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, "Pittsburgh")
        self.assertEqual(team.normalized_location.state_prov, "Pennsylvania")
        self.assertEqual(team.normalized_location.state_prov_short, "PA")
        self.assertEqual(team.normalized_location.country, "United States")
        self.assertEqual(team.normalized_location.country_short, "US")
        self.assertEqual(team.normalized_location.postal_code, "15213")
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(40.4379259, -79.9556424))
        # Disabled until we can get more accurate
        # self.assertEqual(team.normalized_location.name, 'Carnegie Mellon University Field Robotics Center')
        # self.assertEqual(team.normalized_location.formatted_address, 'Pittsburgh, PA 15213, USA')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        # self.assertEqual(team.normalized_location.city, 'Pittsburgh')
        # self.assertEqual(team.normalized_location.state_prov, 'Pennsylvania')
        # self.assertEqual(team.normalized_location.state_prov_short, 'PA')
        # self.assertEqual(team.normalized_location.country, 'United States')
        # self.assertEqual(team.normalized_location.country_short, 'US')
        # self.assertEqual(team.normalized_location.postal_code, '15213')
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(40.4433142, -79.9452154))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_67(self):
        # Team 67 (Multiple schools)
        team = Team(
            id="frc67",
            name="General Motors Milford Proving Ground & Huron Valley Schools",
            city="Highland",
            state_prov="Michigan",
            postalcode="48357",
            country="USA",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, 'Huron Valley Schools')
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, '2390 S Milford Rd, Highland, MI 48357, USA')
        # self.assertEqual(team.normalized_location.street_number, '2390')
        # self.assertEqual(team.normalized_location.street, 'South Milford Road')
        self.assertEqual(team.normalized_location.city, "Highland Charter Township")
        self.assertEqual(team.normalized_location.state_prov, "Michigan")
        self.assertEqual(team.normalized_location.state_prov_short, "MI")
        self.assertEqual(team.normalized_location.country, "United States")
        self.assertEqual(team.normalized_location.country_short, "US")
        self.assertEqual(team.normalized_location.postal_code, "48357")
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(42.6171756, -83.6182952))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_6018(self):
        # Team 6018 (School in China)
        team = Team(
            id="frc6018",
            name="High School Attached to Northwestern Normal University",
            city="Lanzhou",
            state_prov="Gansu",
            postalcode="730070",
            country="China",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, 'High School Attached To Northwest Normal University')
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, '21 Shilidian S St, Anning Qu, Lanzhou Shi, Gansu Sheng, China, 730070')
        # self.assertEqual(team.normalized_location.street_number, '21')
        # self.assertEqual(team.normalized_location.street, 'Shilidian South Street')
        self.assertTrue("Lanzhou" in team.normalized_location.city)
        self.assertTrue("Gansu" in team.normalized_location.state_prov)
        self.assertTrue("Gansu" in team.normalized_location.state_prov_short)
        self.assertEqual(team.normalized_location.country, "China")
        self.assertEqual(team.normalized_location.country_short, "CN")
        self.assertEqual(team.normalized_location.postal_code, "730070")
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(36.09318959999999, 103.7491115))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_6434(self):
        # Team 6434 (School in Australia)
        team = Team(
            id="frc6434",
            name="Bossley Park High School",
            city="Bossley Park",
            state_prov="New South Wales",
            postalcode="2176",
            country="Australia",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, 'Bossley Park High School')
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, '36-44 Prairie Vale Rd, Bossley Park NSW 2176, Australia')
        # self.assertEqual(team.normalized_location.street_number, '36-44')
        # self.assertEqual(team.normalized_location.street, 'Prairie Vale Road')
        self.assertEqual(team.normalized_location.city, "Bossley Park")
        self.assertEqual(team.normalized_location.state_prov, "New South Wales")
        self.assertEqual(team.normalized_location.state_prov_short, "NSW")
        self.assertEqual(team.normalized_location.country, "Australia")
        self.assertEqual(team.normalized_location.country_short, "AU")
        self.assertEqual(team.normalized_location.postal_code, "2176")
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(-33.870024, 150.8753854))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_2122(self):
        # Team 2122 (Complicated team name, wrong postal code)
        team = Team(
            id="frc2122",
            name="Micron Technology, Inc./Hewlett Packard/Boise Schools Educational Foundation/Laura Moore Cunningham Foundation/J.C. Jeker Foundation & Treasure Valley Math/Science",
            city="Boise",
            state_prov="Idaho",
            postalcode="83709",
            country="USA",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, None)
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, 'Boise, ID 83709, USA')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, "Boise")
        self.assertEqual(team.normalized_location.state_prov, "Idaho")
        self.assertEqual(team.normalized_location.state_prov_short, "ID")
        self.assertEqual(team.normalized_location.country, "United States")
        self.assertEqual(team.normalized_location.country_short, "US")
        self.assertEqual(team.normalized_location.postal_code, "83709")
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(43.5516566, -116.29879))
        # Disabled until we can get more accurate
        # self.assertEqual(team.normalized_location.name, 'TVMSC')
        # self.assertEqual(team.normalized_location.formatted_address, '6801 N Gary Ln, Boise, ID 83714, USA')
        # self.assertEqual(team.normalized_location.street_number, '6801')
        # self.assertEqual(team.normalized_location.street, 'North Gary Lane')
        # self.assertEqual(team.normalized_location.city, 'Boise')
        # self.assertEqual(team.normalized_location.state_prov, 'Idaho')
        # self.assertEqual(team.normalized_location.state_prov_short, 'ID')
        # self.assertEqual(team.normalized_location.country, 'United States')
        # self.assertEqual(team.normalized_location.country_short, 'US')
        # self.assertEqual(team.normalized_location.postal_code, '83714')
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(43.68010509999999, -116.2800371))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_3354(self):
        # Team 3354 (Mexican team, special symbols, odd school name)
        team = Team(
            id="frc3354",
            name="Mabe/Bombardier Aerospace Mexico/Coca Cola/Grupo Salinas/Fundacion Azteca/Navex/Red Cross/United Nations/Lego Education/Foundation For a Drug Free World & Tec de Monterrey",
            city="Queretaro",
            state_prov="Quer\xe9taro",
            postalcode="76130",
            country="Mexico",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, None)
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, u'San Pablo, 76130 Santiago de Quer\xe9taro, Qro., Mexico')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, "Santiago de Quer\xe9taro")
        self.assertEqual(team.normalized_location.state_prov, "Quer\xe9taro")
        self.assertEqual(team.normalized_location.state_prov_short, "Qro.")
        self.assertEqual(team.normalized_location.country, "Mexico")
        self.assertEqual(team.normalized_location.country_short, "MX")
        self.assertEqual(team.normalized_location.postal_code, "76130")
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(20.6183707, -100.4185855))
        # Disabled until we can get more accurate
        # self.assertEqual(team.normalized_location.name, u'Tecnol\xf3gico de Monterrey')
        # self.assertEqual(team.normalized_location.formatted_address, u'Epigmenio Gonz\xe1lez 500, San Pablo, 76130 Santiago de Quer\xe9taro, Qro., Mexico')
        # self.assertEqual(team.normalized_location.street_number, '500')
        # self.assertEqual(team.normalized_location.street, u'Epigmenio Gonz\xe1lez')
        # self.assertEqual(team.normalized_location.city, u'Santiago de Quer\xe9taro')
        # self.assertEqual(team.normalized_location.state_prov, u'Quer\xe9taro')
        # self.assertEqual(team.normalized_location.state_prov_short, 'Qro.')
        # self.assertEqual(team.normalized_location.country, 'Mexico')
        # self.assertEqual(team.normalized_location.country_short, 'MX')
        # self.assertEqual(team.normalized_location.postal_code, '76130')
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(20.6133432, -100.4053132))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_3933(self):
        # Team 3933 (Mexican team, special symbols, odd school name)
        team = Team(
            id="frc3933",
            name="General Motors Mexico & Tecnol\xe1gico de Monterrey Campus Santa Fe",
            city="Mexico",
            state_prov="Distrito Federal",
            postalcode="01389",
            country="Mexico",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, None)
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, 'Mexico City, CDMX, Mexico')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, "Mexico City")
        self.assertEqual(team.normalized_location.state_prov, "Mexico City")
        self.assertEqual(team.normalized_location.state_prov_short, "CDMX")
        self.assertEqual(team.normalized_location.country, "Mexico")
        self.assertEqual(team.normalized_location.country_short, "MX")
        self.assertEqual(team.normalized_location.postal_code, None)
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(19.4326077, -99.133208))
        # Disabled until we can get more accurate
        # self.assertEqual(team.normalized_location.name, 'Tec de Monterrey Campus Santa Fe (ITESM)')
        # self.assertEqual(team.normalized_location.formatted_address, u'Av. Carlos Lazo #100, \xc1lvaro Obreg\xf3n, Santa Fe, La Loma, 01389 Ciudad de M\xe9xico, CDMX, Mexico')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        # self.assertEqual(team.normalized_location.city, u'Ciudad de M\xe9xico')
        # self.assertEqual(team.normalized_location.state_prov, u'Ciudad de M\xe9xico')
        # self.assertEqual(team.normalized_location.state_prov_short, 'CDMX')
        # self.assertEqual(team.normalized_location.country, 'Mexico')
        # self.assertEqual(team.normalized_location.country_short, 'MX')
        # self.assertEqual(team.normalized_location.postal_code, '01389')
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(19.3593887, -99.26045889999999))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_6227(self):
        # Team 6227 (Chinese team, odd school name)
        team = Team(
            id="frc6227",
            name="The Middle School Attached to Northwestern Polytechnical University / ROBOTERRA & Family Friends",
            city="Xi'An",
            state_prov="Shaanxi",
            postalcode=None,
            country="China",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, None)
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, 'Xi\'an, Shaanxi, China')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, "Xi'an")
        self.assertEqual(team.normalized_location.state_prov, "Shaanxi")
        self.assertEqual(team.normalized_location.state_prov_short, "Shaanxi")
        self.assertEqual(team.normalized_location.country, "China")
        self.assertEqual(team.normalized_location.country_short, "CN")
        self.assertEqual(team.normalized_location.postal_code, None)
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(34.341575, 108.93977))
        # Disabled until we can get more accurate
        # self.assertEqual(team.normalized_location.name, 'Northwestern Polytechnical University Affiliated Middle School')
        # self.assertEqual(team.normalized_location.formatted_address, '127 Youyi W Rd, ErHuan Lu YanXian ShangYe JingJiDai, Beilin Qu, Xian Shi, Shaanxi Sheng, China, 710000')
        # self.assertEqual(team.normalized_location.street_number, u'127\u53f7')
        # self.assertEqual(team.normalized_location.street, 'Youyi West Road')
        # self.assertEqual(team.normalized_location.city, 'Xian Shi')
        # self.assertEqual(team.normalized_location.state_prov, 'Shaanxi Sheng')
        # self.assertEqual(team.normalized_location.state_prov_short, 'Shaanxi Sheng')
        # self.assertEqual(team.normalized_location.country, 'China')
        # self.assertEqual(team.normalized_location.country_short, 'CN')
        # self.assertEqual(team.normalized_location.postal_code, '710000')
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(34.24073449999999, 108.916593))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_6228(self):
        # Team 6228 (Turkish team, odd school name)
        team = Team(
            id="frc6228",
            name="Ministry of Education/Odeabank/Arena Advertising/Trio Machine/Turkish Airlines/Metalinoks/Sisli Municipality/Hisim Group/Fikret Yuksel Foundation/Metal Yapi & Macka Akif Tuncel Vocational and Technical High School",
            city="Istanbul",
            state_prov="Istanbul",
            postalcode="34367",
            country="Turkey",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, None)
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, u'Harbiye, 34367 \u015ei\u015fli/\u0130stanbul, Turkey')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        self.assertTrue(team.normalized_location.city in {"Istanbul", "\u0130stanbul"})
        self.assertTrue(
            team.normalized_location.state_prov in {"Istanbul", "\u0130stanbul"}
        )
        self.assertTrue(
            team.normalized_location.state_prov_short in {"Istanbul", "\u0130stanbul"}
        )
        self.assertEqual(team.normalized_location.country, "Turkey")
        self.assertEqual(team.normalized_location.country_short, "TR")
        self.assertEqual(team.normalized_location.postal_code, "34367")
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(41.0450373, 28.9921599))
        # Disabled until we can get more accurate
        # self.assertEqual(team.normalized_location.name, u'Ma\xe7ka Akif Tuncel Mesleki ve Teknik Anadolu Lisesi')
        # self.assertEqual(team.normalized_location.formatted_address, u'Harbiye Mh., Harbiye, Ma\xe7ka Caddesi No10, 34367 \u015ei\u015fli/\u0130stanbul, Turkey')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        # self.assertEqual(team.normalized_location.city, u'\u0130stanbul')
        # self.assertEqual(team.normalized_location.state_prov, u'\u0130stanbul')
        # self.assertEqual(team.normalized_location.state_prov_short, u'\u0130stanbul')
        # self.assertEqual(team.normalized_location.country, 'Turkey')
        # self.assertEqual(team.normalized_location.country_short, 'TR')
        # self.assertEqual(team.normalized_location.postal_code, '34367')
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(41.047045, 28.994531))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_6231(self):
        # Team 6231 (Turkish team, odd school name)
        team = Team(
            id="frc6231",
            name="Haydar Ak\u0131n Mesleki Teknik Anadolu L\u0131ses\u0131 & Immib Bahcelievler Erkan Avci Mesleki ve Teknik Anadolu Lisesi",
            city="Istanbul",
            state_prov="Istanbul",
            postalcode=None,
            country="Turkey",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, u'\u0130MM\u0130B Erkan Avc\u0131 Mesleki ve Teknik Anadolu Lisesi')
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, u'Bah\xe7elievler, K\xfclt\xfcr Sk. No:3, . K\xfclt\xfcr Sk. Bah\xe7elievler/\u0130stanbul, Turkey')
        # self.assertEqual(team.normalized_location.street_number, '3')
        # self.assertEqual(team.normalized_location.street, u'K\xfclt\xfcr Sokak')
        self.assertTrue(team.normalized_location.city in {"Istanbul", "\u0130stanbul"})
        self.assertTrue(
            team.normalized_location.state_prov in {"Istanbul", "\u0130stanbul"}
        )
        self.assertTrue(
            team.normalized_location.state_prov_short in {"Istanbul", "\u0130stanbul"}
        )
        self.assertEqual(team.normalized_location.country, "Turkey")
        self.assertEqual(team.normalized_location.country_short, "TR")
        self.assertEqual(team.normalized_location.postal_code, None)
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(40.996236, 28.8618779))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_4403(self):
        # Team 4403 (Turkish team, odd school name)
        team = Team(
            id="frc4403",
            name="MET MEX PE\xd1OLES, S.A. DE C.V. & Tec de Monterrey Campus Laguna",
            city="Torreon",
            state_prov="Coahuila",
            postalcode="27250",
            country="Mexico",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, None)
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, u'Residencial Campestre la Rosita, 27250 Torre\xf3n, Coah., Mexico')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, "Torre\xf3n")
        self.assertEqual(team.normalized_location.state_prov, "Coahuila de Zaragoza")
        self.assertEqual(team.normalized_location.state_prov_short, "Coah.")
        self.assertEqual(team.normalized_location.country, "Mexico")
        self.assertEqual(team.normalized_location.country_short, "MX")
        self.assertEqual(team.normalized_location.postal_code, "27250")
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(25.5232901, -103.4136118))
        # Disabled until we can get more accurate
        # self.assertEqual(team.normalized_location.name, u'Instituto Tecnol\xf3gico de Estudios Superiores de Monterrey')
        # self.assertEqual(team.normalized_location.formatted_address, u'Paseo del Tecnol\xf3gico 751, La Rosita, Amp la Rosita, 27250 Torre\xf3n, Coah., Mexico')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        # self.assertEqual(team.normalized_location.city, u'Torre\xf3n')
        # self.assertEqual(team.normalized_location.state_prov, 'Coahuila de Zaragoza')
        # self.assertEqual(team.normalized_location.state_prov_short, 'Coah.')
        # self.assertEqual(team.normalized_location.country, 'Mexico')
        # self.assertEqual(team.normalized_location.country_short, 'MX')
        # self.assertEqual(team.normalized_location.postal_code, '27250')
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(25.5173546, -103.3976534))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_3211(self):
        # Team 3211 (odd location)
        team = Team(
            id="frc3211",
            name="NRCN / Perrigo / The Yeruham Miami partnership / The Jewish federations of north america / Rashi foundation / Ministry of science / Ministry for the Development of the Negev and Galilee / Automation Yeruham / OPC / Perion / Cimatron / Gazit-Globe / Brand industries / The Yeruham Municipality / Matnas Yeruham / Rotem Industries Ltd. / Ben Gurion University department of mechanical engineering / The Jusidman Center for Science Oriented Youth in Ben-Gurion University & The Yeurham science center & Ort Sapir Yeruham & Belevav Shalem & Kama & IAF Technological College, Be'er Sheva",
            city="Yeruham",
            state_prov="HaDarom (Southern)",
            postalcode="80500",
            country="Israel",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, None)
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, 'Yeruham, Israel')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, "Yeruham")
        self.assertEqual(team.normalized_location.state_prov, "South District")
        self.assertEqual(team.normalized_location.state_prov_short, "South District")
        self.assertEqual(team.normalized_location.country, "Israel")
        self.assertEqual(team.normalized_location.country_short, "IL")
        self.assertEqual(team.normalized_location.postal_code, None)
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(30.987804, 34.929741))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_2398(self):
        # Team 2398
        team = Team(
            id="frc2398",
            name="The Boeing Company/Cherokee Nation & Sequoyah High School",
            city="Tahlequah",
            state_prov="Oklahoma",
            postalcode="74465",
            country="USA",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, 'Sequoyah School')
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, '17091 S Muskogee Ave, Tahlequah, OK 74464, USA')
        # self.assertEqual(team.normalized_location.street_number, '17091')
        # self.assertEqual(team.normalized_location.street, 'South Muskogee Avenue')
        self.assertEqual(team.normalized_location.city, "Tahlequah")
        self.assertEqual(team.normalized_location.state_prov, "Oklahoma")
        self.assertEqual(team.normalized_location.state_prov_short, "OK")
        self.assertEqual(team.normalized_location.country, "United States")
        self.assertEqual(team.normalized_location.country_short, "US")
        self.assertEqual(team.normalized_location.postal_code, "74465")
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(35.8488224, -95.00209149999999))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_simple(self):
        # Only has city, state, country
        team = Team(
            id="frc9999",
            city="San Jose",
            state_prov="CA",
            country="USA",
        )
        LocationHelper.update_team_location(team)
        # self.assertEqual(team.normalized_location.name, None)
        self.assertEqual(team.normalized_location.name, None)
        # self.assertEqual(team.normalized_location.formatted_address, 'San Jose, CA, USA')
        # self.assertEqual(team.normalized_location.street_number, None)
        # self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, "San Jose")
        self.assertEqual(team.normalized_location.state_prov, "California")
        self.assertEqual(team.normalized_location.state_prov_short, "CA")
        self.assertEqual(team.normalized_location.country, "United States")
        self.assertEqual(team.normalized_location.country_short, "US")
        self.assertEqual(team.normalized_location.postal_code, None)
        # self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(37.3382082, -121.8863286))

    @pytest.mark.skipif(not test_google_api_key, reason="No Test API Key")
    @pytest.mark.skip
    def test_team_location_nonsense(self):
        # Nonsense location
        team = Team(
            id="frc9999",
            city="NOTACITY",
            state_prov="NOTASTATE",
            country="NOTACOUNTRY",
        )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, None)
        self.assertEqual(team.normalized_location.formatted_address, None)
        self.assertEqual(team.normalized_location.street_number, None)
        self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, None)
        self.assertEqual(team.normalized_location.state_prov, None)
        self.assertEqual(team.normalized_location.state_prov_short, None)
        self.assertEqual(team.normalized_location.country, None)
        self.assertEqual(team.normalized_location.country_short, None)
        self.assertEqual(team.normalized_location.postal_code, None)
        # self.assertEqual(team.normalized_location.lat_lng, None)


# ---------------------------------------------------------------------------
# Unit tests with mocked Google Maps HTTP (no network, no real API key).
# ---------------------------------------------------------------------------

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
NEARBYSEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
TEXTSEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
TIMEZONE_URL = "https://maps.googleapis.com/maps/api/timezone/json"

SAN_JOSE = LatLng(37.3382, -121.8863)
NEW_YORK = LatLng(40.7128, -74.006)


@pytest.fixture(autouse=True)
def reset_google_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    # The API key is cached on the class once loaded; keep tests independent.
    monkeypatch.setattr(LocationHelper, "GOOGLE_API_KEY", None)


def _put_google_secrets(api_key: str = "test-api-key") -> None:
    Sitevar(id="google.secrets", values_json=json.dumps({"api_key": api_key})).put()


def _qs(request: Any, key: str) -> Optional[str]:
    """First value of a query-string param from a recorded request, case-preserving."""
    values = parse_qs(urlparse(request.url).query, keep_blank_values=True).get(key)
    return values[0] if values else None


def _requests_to(requests_mock: Mocker, url: str) -> List[Any]:
    return [r for r in requests_mock.request_history if r.url.startswith(url)]


def _geocode_result(
    lat: float = SAN_JOSE.lat, lng: float = SAN_JOSE.lon, place_id: str = "geo-place"
) -> Dict[str, Any]:
    # Geocode results carry no "name"
    return {
        "place_id": place_id,
        "geometry": {"location": {"lat": lat, "lng": lng}},
        "types": ["locality", "political"],
    }


def _place(
    name: str,
    place_id: str = "place-1",
    lat: float = SAN_JOSE.lat,
    lng: float = SAN_JOSE.lon,
    types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "place_id": place_id,
        "name": name,
        "geometry": {"location": {"lat": lat, "lng": lng}},
        "types": ["point_of_interest", "establishment"] if types is None else types,
    }


def _place_details(
    name: str = "Leland High School",
    types: Optional[List[str]] = None,
    include_city: bool = True,
    include_state: bool = True,
    formatted_address: str = "6677 Camden Ave, San Jose, CA 95120, USA",
    include_optional: bool = True,
) -> Dict[str, Any]:
    components: List[Dict[str, Any]] = [
        {"types": ["street_number"], "long_name": "6677", "short_name": "6677"},
        {"types": ["route"], "long_name": "Camden Avenue", "short_name": "Camden Ave"},
        {
            "types": ["administrative_area_level_2", "political"],  # ignored
            "long_name": "Santa Clara County",
            "short_name": "Santa Clara County",
        },
        {
            "types": ["country", "political"],
            "long_name": "United States",
            "short_name": "US",
        },
        {"types": ["postal_code"], "long_name": "95120", "short_name": "95120"},
    ]
    if include_city:
        components.append(
            {
                "types": ["locality", "political"],
                "long_name": "San Jose",
                "short_name": "San Jose",
            }
        )
    if include_state:
        components.append(
            {
                "types": ["administrative_area_level_1", "political"],
                "long_name": "California",
                "short_name": "CA",
            }
        )
    details: Dict[str, Any] = {
        "address_components": components,
        "formatted_address": formatted_address,
    }
    if include_optional:
        details["geometry"] = {"location": {"lat": 37.2, "lng": -121.9}}
        details["name"] = name
        details["types"] = (
            ["school", "point_of_interest", "establishment"] if types is None else types
        )
    return details


def _mock_geocode(
    requests_mock: Mocker, by_address: Dict[str, List[Dict[str, Any]]]
) -> None:
    def _cb(request: Any, context: Any) -> Dict[str, Any]:
        results = by_address.get(_qs(request, "address") or "")
        if results:
            return {"status": "OK", "results": results}
        return {"status": "ZERO_RESULTS", "results": []}

    requests_mock.get(GEOCODE_URL, json=_cb)


def _mock_placesearch(
    requests_mock: Mocker,
    nearby: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    text: Optional[Dict[str, List[Dict[str, Any]]]] = None,
) -> None:
    def _make(
        by_query: Dict[str, List[Dict[str, Any]]], param: str
    ) -> Any:  # requests_mock json callback
        def _cb(request: Any, context: Any) -> Dict[str, Any]:
            results = by_query.get(_qs(request, param) or "")
            if results:
                return {"status": "OK", "results": results}
            return {"status": "ZERO_RESULTS", "results": []}

        return _cb

    requests_mock.get(NEARBYSEARCH_URL, json=_make(nearby or {}, "keyword"))
    requests_mock.get(TEXTSEARCH_URL, json=_make(text or {}, "query"))


def _mock_place_details(
    requests_mock: Mocker, by_place_id: Dict[str, Dict[str, Any]]
) -> None:
    def _cb(request: Any, context: Any) -> Dict[str, Any]:
        result = by_place_id.get(_qs(request, "placeid") or "")
        if result:
            return {"status": "OK", "result": result}
        return {"status": "ZERO_RESULTS"}

    requests_mock.get(PLACE_DETAILS_URL, json=_cb)


# --- get_similarity ---------------------------------------------------------


def test_get_similarity_identical() -> None:
    assert (
        LocationHelper.get_similarity("Leland High School", "Leland High School") == 1
    )


def test_get_similarity_ignores_case_and_surrounding_whitespace() -> None:
    assert (
        LocationHelper.get_similarity("  LELAND high School ", "leland high school")
        == 1
    )


def test_get_similarity_ignores_word_order_and_separators() -> None:
    assert LocationHelper.get_similarity("san-jose, ca", "ca san jose") == 1


def test_get_similarity_dissimilar_strings_score_low() -> None:
    assert LocationHelper.get_similarity("Leland High School", "Zebra Quantum") < 0.3


def test_get_similarity_matches_acronym() -> None:
    assert LocationHelper.get_similarity("lhs", "Leland High School") == 1
    assert LocationHelper.get_similarity("Leland High School", "lhs") == 1


# --- get_event_location / update_event_location ------------------------------


def _event(**kwargs: Any) -> Event:
    defaults: Dict[str, Any] = dict(
        id="2016test", year=2016, city="San Jose", state_prov="CA", country="USA"
    )
    defaults.update(kwargs)
    return Event(**defaults)


def test_get_event_location_uses_high_scoring_info(
    caplog: pytest.LogCaptureFixture,
) -> None:
    info: LocationInfo = {
        "name": "Leland High School",
        "lat": 37.0,
        "lng": -122.0,
        "formatted_address": "6677 Camden Ave, San Jose, CA 95120, USA",
        "city": "San Jose",
        "place_id": "place-1",
    }
    with (
        patch.object(
            LocationHelper, "get_event_location_info", return_value=(info, 0.95)
        ),
        patch.object(LocationHelper, "google_maps_geocode") as geocode_mock,
    ):
        with caplog.at_level(logging.INFO):
            location = LocationHelper.get_event_location(_event())

    geocode_mock.assert_not_called()
    assert location is not None
    assert location.name == "Leland High School"
    assert location.city == "San Jose"
    assert location.place_id == "place-1"
    assert location.lat_lng == ndb.GeoPt(37.0, -122.0)
    score_records = [r for r in caplog.records if "location score: 0.95" in r.message]
    assert len(score_records) == 1
    assert score_records[0].levelno == logging.INFO


def test_get_event_location_low_score_warns(caplog: pytest.LogCaptureFixture) -> None:
    info: LocationInfo = {"name": "Somewhere", "lat": 1.0, "lng": 2.0}
    with patch.object(
        LocationHelper, "get_event_location_info", return_value=(info, 0.5)
    ):
        with caplog.at_level(logging.INFO):
            location = LocationHelper.get_event_location(_event())

    assert location is not None
    assert location.name == "Somewhere"
    score_records = [r for r in caplog.records if "location score: 0.5" in r.message]
    assert len(score_records) == 1
    assert score_records[0].levelno == logging.WARNING


def test_get_event_location_falls_back_to_geocode(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    _put_google_secrets()
    _mock_geocode(requests_mock, {"San Jose, CA, USA": [_geocode_result()]})
    _mock_place_details(requests_mock, {"geo-place": _place_details()})

    with patch.object(LocationHelper, "get_event_location_info", return_value=({}, 0)):
        location = LocationHelper.get_event_location(_event())

    assert "Falling back to location only for event 2016test" in caplog.text
    assert location is not None
    assert location.place_id == "geo-place"
    assert location.name == "Leland High School"  # auto-filled from place details
    assert location.city == "San Jose"
    assert location.lat_lng == ndb.GeoPt(37.2, -121.9)  # auto-filled geometry


def test_get_event_location_geocode_failure_yields_empty_location(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    _mock_geocode(requests_mock, {})

    with patch.object(LocationHelper, "get_event_location_info", return_value=({}, 0)):
        location = LocationHelper.get_event_location(_event())

    assert "Event 2016test location failed!" in caplog.text
    assert location is not None
    assert location.name is None
    assert location.lat_lng is None
    assert location.city is None


def test_update_event_location_skips_event_without_location() -> None:
    event = Event(id="2016test", year=2016)
    with patch.object(LocationHelper, "get_event_location") as get_mock:
        LocationHelper.update_event_location(event)
    get_mock.assert_not_called()
    assert event.normalized_location is None


def test_update_event_location_only_sets_once() -> None:
    event = _event(normalized_location=Location(name="Existing"))
    with patch.object(LocationHelper, "get_event_location") as get_mock:
        LocationHelper.update_event_location(event)
    get_mock.assert_not_called()
    assert none_throws(event.normalized_location).name == "Existing"


def test_update_event_location_sets_normalized_location() -> None:
    event = _event()
    with patch.object(
        LocationHelper, "get_event_location", return_value=Location(name="Found")
    ):
        LocationHelper.update_event_location(event)
    assert none_throws(event.normalized_location).name == "Found"


# --- get_event_location_info -------------------------------------------------


def test_get_event_location_info_without_lat_lng(requests_mock: Mocker) -> None:
    _put_google_secrets()
    _mock_geocode(requests_mock, {})
    _mock_placesearch(requests_mock)

    info, score = LocationHelper.get_event_location_info(_event(venue="Leland"))

    assert (info, score) == ({}, 0)
    assert _requests_to(requests_mock, NEARBYSEARCH_URL) == []
    assert _requests_to(requests_mock, TEXTSEARCH_URL) == []


def test_get_event_location_info_perfect_match_returns_early(
    requests_mock: Mocker,
) -> None:
    _put_google_secrets()
    _mock_geocode(requests_mock, {"San Jose, CA, USA": [_geocode_result()]})
    _mock_placesearch(
        requests_mock,
        nearby={"Leland High School": [_place("Leland High School")]},
        text={"Leland High School": [_place("Leland High School", place_id="dup")]},
    )
    _mock_place_details(
        requests_mock,
        {"place-1": _place_details(), "dup": _place_details()},
    )

    info, score = LocationHelper.get_event_location_info(
        _event(venue="Leland High School")
    )

    assert score == 1
    assert info["place_id"] == "place-1"
    assert info["name"] == "Leland High School"
    assert info["city"] == "San Jose"
    # Both searches are issued up front for the query before results are scored
    assert [
        _qs(r, "keyword") for r in _requests_to(requests_mock, NEARBYSEARCH_URL)
    ] == ["Leland High School"]
    assert [_qs(r, "query") for r in _requests_to(requests_mock, TEXTSEARCH_URL)] == [
        "Leland High School"
    ]


def test_get_event_location_info_keeps_best_partial_match(
    requests_mock: Mocker,
) -> None:
    _put_google_secrets()
    _mock_geocode(requests_mock, {"San Jose, CA, USA": [_geocode_result()]})
    venue_address = "Leland High School\n6677 Camden Ave\nSan Jose, CA 95120"
    _mock_placesearch(
        requests_mock,
        nearby={
            # Not a point of interest -> scores 0, never becomes "best"
            "Leland High School 6677 Camden Ave San Jose, CA 95120": [
                _place("Camden Park", place_id="park", types=["park"])
            ],
        },
        text={"Leland High School": [_place("Leland Academy", place_id="academy")]},
    )
    _mock_place_details(
        requests_mock,
        {
            "park": _place_details(name="Camden Park", types=["park"]),
            "academy": _place_details(name="Leland Academy"),
        },
    )

    info, score = LocationHelper.get_event_location_info(
        _event(venue="Leland High School", venue_address=venue_address)
    )

    assert info["place_id"] == "academy"
    assert info["name"] == "Leland Academy"
    assert 0 < score < 1
    expected_queries = [
        "Leland High School 6677 Camden Ave San Jose, CA 95120",
        "Leland High School",
        "6677 Camden Ave San Jose, CA 95120",
        "San Jose, CA 95120",
    ]
    assert [
        _qs(r, "keyword") for r in _requests_to(requests_mock, NEARBYSEARCH_URL)
    ] == expected_queries
    assert [
        _qs(r, "query") for r in _requests_to(requests_mock, TEXTSEARCH_URL)
    ] == expected_queries


def test_get_event_location_info_no_places_found(requests_mock: Mocker) -> None:
    _put_google_secrets()
    _mock_geocode(requests_mock, {"San Jose, CA, USA": [_geocode_result()]})
    _mock_placesearch(requests_mock)

    info, score = LocationHelper.get_event_location_info(
        _event(venue_address="Only One Line")
    )

    assert (info, score) == ({}, 0)
    # A single-line venue_address yields empty follow-up queries, which are skipped
    assert [
        _qs(r, "keyword") for r in _requests_to(requests_mock, NEARBYSEARCH_URL)
    ] == ["Only One Line"]


# --- compute_event_location_score -------------------------------------------


def _event_info(
    name: str,
    lat_lng: LatLng = SAN_JOSE,
    types: Optional[List[str]] = None,
    formatted_address: str = "6677 Camden Ave, San Jose, CA 95120, USA",
) -> LocationInfo:
    # LocationInfo annotates `types` as str, but the helper stores the list from
    # the Google Maps result, so build it the way the helper does.
    return cast(
        LocationInfo,
        {
            "name": name,
            "lat": lat_lng.lat,
            "lng": lat_lng.lon,
            "types": ["point_of_interest"] if types is None else types,
            "formatted_address": formatted_address,
        },
    )


def test_compute_event_location_score_shenzhen_special_case() -> None:
    assert (
        LocationHelper.compute_event_location_score(
            "Shenzhen Stadium", _event_info("Shenzhen Stadium"), SAN_JOSE
        )
        == 0
    )
    assert (
        LocationHelper.compute_event_location_score(
            "Shenzhen University Town Sports Center",
            _event_info("Shenzhen University Town Sports Center"),
            SAN_JOSE,
        )
        == 1
    )


def test_compute_event_location_score_too_far_away() -> None:
    assert (
        LocationHelper.compute_event_location_score(
            "Leland High School", _event_info("Leland High School", NEW_YORK), SAN_JOSE
        )
        == 0
    )


def test_compute_event_location_score_point_of_interest() -> None:
    assert (
        LocationHelper.compute_event_location_score(
            "Leland High School", _event_info("Leland High School"), SAN_JOSE
        )
        == 1
    )


def test_compute_event_location_score_premise_partial_match() -> None:
    info = _event_info("Leland Academy", types=["premise"])
    score = LocationHelper.compute_event_location_score(
        "Leland High School", info, SAN_JOSE
    )
    expected = pow(
        max(
            LocationHelper.get_similarity("Leland High School", "Leland Academy"),
            LocationHelper.get_similarity(
                "Leland High School", info["formatted_address"]
            ),
        ),
        1.0 / 3,
    )
    assert 0 < score < 1
    assert score == pytest.approx(expected)  # pyre-ignore[16]


def test_compute_event_location_score_not_point_of_interest() -> None:
    assert (
        LocationHelper.compute_event_location_score(
            "Leland High School",
            _event_info("Leland High School", types=["school"]),
            SAN_JOSE,
        )
        == 0
    )


# --- update_team_location ---------------------------------------------------


def _team(**kwargs: Any) -> Team:
    defaults: Dict[str, Any] = dict(
        id="frc604", team_number=604, city="San Jose", state_prov="CA", country="USA"
    )
    defaults.update(kwargs)
    return Team(**defaults)


def test_update_team_location_skips_team_without_location() -> None:
    team = Team(id="frc604", team_number=604)
    with patch.object(LocationHelper, "google_maps_geocode") as geocode_mock:
        LocationHelper.update_team_location(team)
    geocode_mock.assert_not_called()
    assert team.normalized_location is None


def test_update_team_location_geocodes_full_location(requests_mock: Mocker) -> None:
    _put_google_secrets()
    team = _team(postalcode="95120")
    _mock_geocode(requests_mock, {"San Jose, CA 95120, USA": [_geocode_result()]})
    details = _place_details()
    _mock_place_details(requests_mock, {"geo-place": details})

    LocationHelper.update_team_location(team)

    location = team.normalized_location
    assert location.name is None  # auto_fill=False and geocode results have no name
    assert location.lat_lng == ndb.GeoPt(SAN_JOSE.lat, SAN_JOSE.lon)  # not auto-filled
    assert location.formatted_address == "6677 Camden Ave, San Jose, CA 95120, USA"
    assert location.street_number == "6677"
    assert location.street == "Camden Avenue"
    assert location.city == "San Jose"
    assert location.state_prov == "California"
    assert location.state_prov_short == "CA"
    assert location.country == "United States"
    assert location.country_short == "US"
    assert location.postal_code == "95120"
    assert location.place_id == "geo-place"
    assert location.place_details == details


def test_update_team_location_falls_back_to_city_country(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    _put_google_secrets()
    team = _team(city="Nowhere", state_prov="ZZ", country="Narnia")
    _mock_geocode(
        requests_mock, {"Nowhere Narnia": [_geocode_result(place_id="fallback")]}
    )
    _mock_place_details(requests_mock, {"fallback": _place_details(include_city=False)})

    LocationHelper.update_team_location(team)

    assert "Falling back to city/country only for team frc604" in caplog.text
    assert [_qs(r, "address") for r in _requests_to(requests_mock, GEOCODE_URL)] == [
        "Nowhere, ZZ, Narnia",
        "Nowhere Narnia",
    ]
    location = team.normalized_location
    assert location.place_id == "fallback"
    assert location.city == "California"  # no locality -> falls back to state_prov


def test_update_team_location_all_lookups_fail(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    team = Team(id="frc604", team_number=604, state_prov="ZZ")  # no city/country
    _mock_geocode(requests_mock, {})

    LocationHelper.update_team_location(team)

    assert "Team frc604 location failed!" in caplog.text
    assert [_qs(r, "address") for r in _requests_to(requests_mock, GEOCODE_URL)] == [
        "ZZ",
        " ",
    ]
    location = team.normalized_location
    assert location is not None
    assert location.lat_lng is None
    assert location.city is None
    assert location.place_id is None


# --- build_normalized_location ----------------------------------------------


def test_build_normalized_location_full() -> None:
    details = {"anything": "goes"}
    # LocationInfo annotates `postal_code` as int, but the helper stores the
    # long_name string from place details (and Location.postal_code is a string).
    info = cast(
        LocationInfo,
        {
            "name": "Leland High School",
            "formatted_address": "6677 Camden Ave, San Jose, CA 95120, USA",
            "lat": 37.2,
            "lng": -121.9,
            "street_number": "6677",
            "street": "Camden Avenue",
            "city": "San Jose",
            "state_prov": "California",
            "state_prov_short": "CA",
            "country": "United States",
            "country_short": "US",
            "postal_code": "95120",
            "place_id": "place-1",
            "place_details": details,
        },
    )
    location = LocationHelper.build_normalized_location(info)
    assert location.name == "Leland High School"
    assert location.formatted_address == "6677 Camden Ave, San Jose, CA 95120, USA"
    assert location.lat_lng == ndb.GeoPt(37.2, -121.9)
    assert location.street_number == "6677"
    assert location.street == "Camden Avenue"
    assert location.city == "San Jose"
    assert location.state_prov == "California"
    assert location.state_prov_short == "CA"
    assert location.country == "United States"
    assert location.country_short == "US"
    assert location.postal_code == "95120"
    assert location.place_id == "place-1"
    assert location.place_details == details


def test_build_normalized_location_empty() -> None:
    location = LocationHelper.build_normalized_location({})
    assert location.name is None
    assert location.lat_lng is None
    assert location.place_details is None


def test_build_normalized_location_requires_both_lat_and_lng() -> None:
    assert LocationHelper.build_normalized_location({"lat": 1.0}).lat_lng is None
    assert LocationHelper.build_normalized_location({"lng": 1.0}).lat_lng is None


# --- get_team_location_info -------------------------------------------------


def test_get_team_location_info_without_lat_lng(requests_mock: Mocker) -> None:
    _put_google_secrets()
    _mock_geocode(requests_mock, {})
    _mock_placesearch(requests_mock)

    info, score = LocationHelper.get_team_location_info(_team(name="Leland"))

    assert (info, score) == ({}, 0)
    assert _requests_to(requests_mock, NEARBYSEARCH_URL) == []


def test_get_team_location_info_perfect_match_returns_early(
    requests_mock: Mocker,
) -> None:
    _put_google_secrets()
    _mock_geocode(requests_mock, {"San Jose, CA, USA": [_geocode_result()]})
    _mock_placesearch(
        requests_mock,
        nearby={
            "Leland High School": [
                _place("Leland High School", types=["school"]),
                _place("Never Scored", place_id="never", types=["school"]),
            ]
        },
    )
    _mock_place_details(
        requests_mock,
        {
            "place-1": _place_details(name="Leland High School", types=["school"]),
            "never": _place_details(name="Never Scored", types=["school"]),
        },
    )

    info, score = LocationHelper.get_team_location_info(
        _team(name="Leland High School")
    )

    assert score == 1
    assert info["place_id"] == "place-1"
    assert _requests_to(requests_mock, TEXTSEARCH_URL) == []
    assert [
        _qs(r, "placeid") for r in _requests_to(requests_mock, PLACE_DETAILS_URL)
    ] == ["place-1"]


def test_get_team_location_info_textsearch_keeps_best_match(
    requests_mock: Mocker,
) -> None:
    _put_google_secrets()
    _mock_geocode(requests_mock, {"San Jose, CA, USA": [_geocode_result()]})
    _mock_placesearch(
        requests_mock,
        text={
            " Leland High School": [
                _place("Leland Academy", place_id="academy", types=["school"]),
                _place("Leland High School", place_id="exact", types=["school"]),
            ],
            # Exact name match but j >= 2 and not a school: 1 * 0.9 * 0.9 = 0.81
            "Google": [_place("Google", place_id="google", types=["establishment"])],
        },
    )
    _mock_place_details(
        requests_mock,
        {
            "academy": _place_details(name="Leland Academy", types=["school"]),
            "exact": _place_details(name="Leland High School", types=["school"]),
            "google": _place_details(name="Google", types=["establishment"]),
        },
    )

    info, score = LocationHelper.get_team_location_info(
        _team(name="Google/Cisco & Leland High School"), textsearch=True
    )

    # Exact match at rank 1 (i=1) is discounted by 0.9 and beats the partial match
    assert info["place_id"] == "exact"
    assert score == pytest.approx(0.9)  # pyre-ignore[16]
    assert _requests_to(requests_mock, NEARBYSEARCH_URL) == []
    assert [_qs(r, "query") for r in _requests_to(requests_mock, TEXTSEARCH_URL)] == [
        " Leland High School",
        "Cisco & Leland High School",
        "Google/Cisco ",
        "Google",
    ]


@pytest.mark.parametrize(
    "name, expected_queries",
    [
        # split1[0] = "A/B/C/D " has 3 slashes -> filtered by MAX_SPLIT
        ("A/B/C/D & E", [" E", "D & E", "A"]),
        # No separators: every split yields the same string, de-duplicated
        ("Leland High School", ["Leland High School"]),
        # No name -> nothing to search for
        (None, []),
    ],
)
def test_get_team_location_info_possible_names(
    name: Optional[str], expected_queries: List[str]
) -> None:
    with (
        patch.object(LocationHelper, "get_lat_lng", return_value=SAN_JOSE),
        patch.object(LocationHelper, "google_maps_placesearch", return_value=[]) as m,
    ):
        info, score = LocationHelper.get_team_location_info(_team(name=name))

    assert (info, score) == ({}, 0)
    assert [call.args[0] for call in m.call_args_list] == expected_queries


# --- compute_team_location_score --------------------------------------------


def test_compute_team_location_score_too_far_away() -> None:
    info = _event_info("Leland High School", NEW_YORK, types=["school"])
    assert (
        LocationHelper.compute_team_location_score("Leland High School", info, SAN_JOSE)
        == 0
    )


def test_compute_team_location_score_school_exact_match() -> None:
    info = _event_info("Leland High School", types=["school"])
    assert (
        LocationHelper.compute_team_location_score("Leland High School", info, SAN_JOSE)
        == 1
    )


def test_compute_team_location_score_university_ignores_school_words() -> None:
    info = _event_info("Leland", types=["university"])
    assert (
        LocationHelper.compute_team_location_score("Leland High School", info, SAN_JOSE)
        == 1
    )


def test_compute_team_location_score_non_school_discounted() -> None:
    info = _event_info("Leland High School", types=["establishment"])
    score = LocationHelper.compute_team_location_score(
        "Leland High School", info, SAN_JOSE
    )
    assert score == pytest.approx(0.9)  # pyre-ignore[16]


def test_compute_team_location_score_partial_match() -> None:
    info = _event_info("Leland Academy", types=["school"])
    score = LocationHelper.compute_team_location_score(
        "Leland High School", info, SAN_JOSE
    )
    assert score == pytest.approx(  # pyre-ignore[16]
        pow(LocationHelper.get_similarity("leland  ", "leland academy"), 0.7)
    )
    assert 0 < score < 1


# --- construct_location_info ------------------------------------------------


def test_construct_location_info_without_place_details(requests_mock: Mocker) -> None:
    _put_google_secrets()
    _mock_place_details(requests_mock, {})

    info = LocationHelper.construct_location_info(_place("Leland High School"))

    assert info == {
        "place_id": "place-1",
        "lat": SAN_JOSE.lat,
        "lng": SAN_JOSE.lon,
        "name": "Leland High School",
        "types": ["point_of_interest", "establishment"],
    }


def test_construct_location_info_auto_fills_from_place_details(
    requests_mock: Mocker,
) -> None:
    _put_google_secrets()
    details = _place_details(name="Leland High School (Details)")
    _mock_place_details(requests_mock, {"place-1": details})

    info = LocationHelper.construct_location_info(_place("Leland High School"))

    assert info == {
        "place_id": "place-1",
        "lat": 37.2,
        "lng": -121.9,
        "name": "Leland High School (Details)",
        "types": ["school", "point_of_interest", "establishment"],
        "street_number": "6677",
        "street": "Camden Avenue",
        "city": "San Jose",
        "state_prov": "California",
        "state_prov_short": "CA",
        "country": "United States",
        "country_short": "US",
        "postal_code": "95120",
        "formatted_address": "6677 Camden Ave, San Jose, CA 95120, USA",
        "place_details": details,
    }


def test_construct_location_info_without_auto_fill(requests_mock: Mocker) -> None:
    _put_google_secrets()
    _mock_place_details(
        requests_mock, {"geo-place": _place_details(name="Leland High School")}
    )

    info = LocationHelper.construct_location_info(_geocode_result(), auto_fill=False)

    assert info["lat"] == SAN_JOSE.lat
    assert info["lng"] == SAN_JOSE.lon
    assert info["name"] is None
    assert info["types"] == ["locality", "political"]
    assert info["city"] == "San Jose"
    assert info["formatted_address"] == "6677 Camden Ave, San Jose, CA 95120, USA"


def test_construct_location_info_auto_fill_tolerates_sparse_details(
    requests_mock: Mocker,
) -> None:
    _put_google_secrets()
    _mock_place_details(
        requests_mock,
        {
            "place-1": _place_details(
                include_city=False, include_state=False, include_optional=False
            )
        },
    )

    info = LocationHelper.construct_location_info(_place("Leland High School"))

    assert info["lat"] == SAN_JOSE.lat
    assert info["name"] == "Leland High School"
    assert info["types"] == ["point_of_interest", "establishment"]
    assert "city" not in info
    assert "state_prov" not in info
    assert info["country"] == "United States"


def test_construct_location_info_uses_state_when_no_city(
    requests_mock: Mocker,
) -> None:
    _put_google_secrets()
    _mock_place_details(requests_mock, {"place-1": _place_details(include_city=False)})

    info = LocationHelper.construct_location_info(_place("Leland High School"))

    assert info["city"] == "California"
    assert info["state_prov"] == "California"


# --- google_maps_placesearch ------------------------------------------------


def test_placesearch_without_sitevar(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    requests_mock.get(NEARBYSEARCH_URL, json={"status": "OK", "results": [_place("x")]})

    assert LocationHelper.google_maps_placesearch("Leland", SAN_JOSE) == []

    assert requests_mock.call_count == 0
    assert "Must have sitevar" in caplog.text
    assert LocationHelper.GOOGLE_API_KEY is None


def test_placesearch_loads_key_from_sitevar_and_skips_empty_query(
    requests_mock: Mocker,
) -> None:
    _put_google_secrets("sitevar-key")
    requests_mock.get(NEARBYSEARCH_URL, json={"status": "OK", "results": [_place("x")]})

    assert LocationHelper.google_maps_placesearch("", SAN_JOSE) == []

    assert LocationHelper.GOOGLE_API_KEY == "sitevar-key"
    assert requests_mock.call_count == 0


def test_placesearch_nearby_ok_and_cached(requests_mock: Mocker) -> None:
    _put_google_secrets("sitevar-key")
    places = [_place("Leland High School")]
    requests_mock.get(NEARBYSEARCH_URL, json={"status": "OK", "results": places})

    assert LocationHelper.google_maps_placesearch("Leland", SAN_JOSE) == places
    assert LocationHelper.google_maps_placesearch("Leland", SAN_JOSE) == places

    assert requests_mock.call_count == 1
    request = requests_mock.request_history[0]
    assert _qs(request, "key") == "sitevar-key"
    assert _qs(request, "location") == "37.3382,-121.8863"
    assert _qs(request, "radius") == "25000"
    assert _qs(request, "keyword") == "Leland"
    assert _qs(request, "query") is None


def test_placesearch_textsearch_uses_query_param(requests_mock: Mocker) -> None:
    _put_google_secrets()
    places = [_place("Leland High School")]
    requests_mock.get(TEXTSEARCH_URL, json={"status": "OK", "results": places})

    assert (
        LocationHelper.google_maps_placesearch("Leland", SAN_JOSE, textsearch=True)
        == places
    )

    request = requests_mock.request_history[0]
    assert _qs(request, "query") == "Leland"
    assert _qs(request, "keyword") is None


def test_placesearch_uses_preloaded_class_key(
    requests_mock: Mocker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(LocationHelper, "GOOGLE_API_KEY", "preloaded")
    requests_mock.get(NEARBYSEARCH_URL, json={"status": "OK", "results": []})

    LocationHelper.google_maps_placesearch("Leland", SAN_JOSE)

    assert _qs(requests_mock.request_history[0], "key") == "preloaded"


def test_placesearch_zero_results_cached(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    _put_google_secrets()
    requests_mock.get(NEARBYSEARCH_URL, json={"status": "ZERO_RESULTS", "results": []})

    with caplog.at_level(logging.INFO):
        assert LocationHelper.google_maps_placesearch("Leland", SAN_JOSE) == []
        assert LocationHelper.google_maps_placesearch("Leland", SAN_JOSE) == []

    assert requests_mock.call_count == 1
    assert "No nearbysearch results for query: Leland" in caplog.text


def test_placesearch_error_status(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    _put_google_secrets()
    requests_mock.get(NEARBYSEARCH_URL, json={"status": "REQUEST_DENIED"})

    assert LocationHelper.google_maps_placesearch("Leland", SAN_JOSE) == []
    assert "nearbysearch failed with query: Leland" in caplog.text


def test_placesearch_http_error(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    _put_google_secrets()
    requests_mock.get(TEXTSEARCH_URL, status_code=500)

    assert (
        LocationHelper.google_maps_placesearch("Leland", SAN_JOSE, textsearch=True)
        == []
    )
    assert "textsearch failed with query: Leland" in caplog.text


def test_placesearch_request_exception(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    _put_google_secrets()
    requests_mock.get(NEARBYSEARCH_URL, exc=requests.exceptions.ConnectTimeout)

    assert LocationHelper.google_maps_placesearch("Leland", SAN_JOSE) == []
    assert "urlfetch for nearbysearch request failed with query: Leland" in caplog.text


# --- google_maps_place_details ----------------------------------------------


def test_place_details_without_sitevar(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    requests_mock.get(PLACE_DETAILS_URL, json={"status": "OK", "result": {}})

    assert LocationHelper.google_maps_place_details("place-1") is None

    assert requests_mock.call_count == 0
    assert "Must have sitevar" in caplog.text


def test_place_details_ok_and_cached(requests_mock: Mocker) -> None:
    _put_google_secrets("sitevar-key")
    details = _place_details()
    requests_mock.get(PLACE_DETAILS_URL, json={"status": "OK", "result": details})

    assert LocationHelper.google_maps_place_details("place-1") == details
    assert LocationHelper.google_maps_place_details("place-1") == details

    assert requests_mock.call_count == 1
    request = requests_mock.request_history[0]
    assert _qs(request, "placeid") == "place-1"
    assert _qs(request, "key") == "sitevar-key"


def test_place_details_zero_results(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    _put_google_secrets()
    requests_mock.get(PLACE_DETAILS_URL, json={"status": "ZERO_RESULTS"})

    with caplog.at_level(logging.INFO):
        assert LocationHelper.google_maps_place_details("place-1") is None
    assert "No place_details result for place_id: place-1" in caplog.text


def test_place_details_error_status(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    _put_google_secrets()
    requests_mock.get(PLACE_DETAILS_URL, json={"status": "INVALID_REQUEST"})

    assert LocationHelper.google_maps_place_details("place-1") is None
    assert "Placedetails failed with place_id: place-1." in caplog.text


def test_place_details_http_error(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    _put_google_secrets()
    requests_mock.get(PLACE_DETAILS_URL, status_code=503)

    assert LocationHelper.google_maps_place_details("place-1") is None
    assert "Placedetails failed with place_id: place-1." in caplog.text


def test_place_details_request_exception(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    _put_google_secrets()
    requests_mock.get(PLACE_DETAILS_URL, exc=requests.exceptions.ConnectionError)

    assert LocationHelper.google_maps_place_details("place-1") is None
    assert "urlfetch for place_details request failed with place_id: place-1." in (
        caplog.text
    )


# --- get_lat_lng / google_maps_geocode --------------------------------------


def test_get_lat_lng(requests_mock: Mocker) -> None:
    _mock_geocode(requests_mock, {"San Jose, CA": [_geocode_result()]})

    result = none_throws(LocationHelper.get_lat_lng("San Jose, CA"))

    assert result == LatLng(SAN_JOSE.lat, SAN_JOSE.lon)
    assert isinstance(result.lat, float)
    assert isinstance(result.lon, float)


def test_get_lat_lng_no_results(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    _mock_geocode(requests_mock, {})

    assert LocationHelper.get_lat_lng("Nowhere") is None
    assert "location get_lat_lng failed!" in caplog.text


def test_geocode_empty_location(requests_mock: Mocker) -> None:
    _mock_geocode(requests_mock, {})

    assert LocationHelper.google_maps_geocode(None) == []
    assert LocationHelper.google_maps_geocode("") == []
    assert requests_mock.call_count == 0


def test_geocode_without_sitevar_omits_key(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    results = [_geocode_result()]
    requests_mock.get(GEOCODE_URL, json={"status": "OK", "results": results})

    assert LocationHelper.google_maps_geocode("San Jose, CA") == results

    request = requests_mock.request_history[0]
    assert _qs(request, "address") == "San Jose, CA"
    assert _qs(request, "sensor") == "false"
    assert _qs(request, "key") is None
    assert "Missing sitevar" in caplog.text


def test_geocode_with_sitevar_sends_key_and_caches(requests_mock: Mocker) -> None:
    _put_google_secrets("sitevar-key")
    results = [_geocode_result()]
    requests_mock.get(GEOCODE_URL, json={"status": "OK", "results": results})

    assert LocationHelper.google_maps_geocode("San Jose, CA") == results
    assert LocationHelper.google_maps_geocode("San Jose, CA") == results

    assert requests_mock.call_count == 1
    assert _qs(requests_mock.request_history[0], "key") == "sitevar-key"


def test_geocode_zero_results(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    requests_mock.get(GEOCODE_URL, json={"status": "ZERO_RESULTS", "results": []})

    with caplog.at_level(logging.INFO):
        assert LocationHelper.google_maps_geocode("Nowhere") == []
    assert "No geocode results for location: Nowhere" in caplog.text


def test_geocode_error_status(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    requests_mock.get(GEOCODE_URL, json={"status": "OVER_QUERY_LIMIT"})

    assert LocationHelper.google_maps_geocode("San Jose, CA") == []
    assert "Geocoding failed!" in caplog.text


def test_geocode_http_error(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    requests_mock.get(GEOCODE_URL, status_code=500)

    assert LocationHelper.google_maps_geocode("San Jose, CA") == []
    assert "Geocoding failed for location San Jose, CA." in caplog.text


def test_geocode_request_exception(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    requests_mock.get(GEOCODE_URL, exc=requests.exceptions.ConnectionError)

    assert LocationHelper.google_maps_geocode("San Jose, CA") == []
    assert "urlfetch for geocode request failed for location San Jose, CA." in (
        caplog.text
    )


# --- get_timezone_id --------------------------------------------------------


def test_get_timezone_id_geocode_failure(requests_mock: Mocker) -> None:
    _mock_geocode(requests_mock, {})
    requests_mock.get(TIMEZONE_URL, json={"timeZoneId": "America/Los_Angeles"})

    assert LocationHelper.get_timezone_id("Nowhere") is None
    assert _requests_to(requests_mock, TIMEZONE_URL) == []


def test_get_timezone_id_from_location(requests_mock: Mocker) -> None:
    _mock_geocode(requests_mock, {"San Jose, CA": [_geocode_result()]})
    requests_mock.get(TIMEZONE_URL, json={"timeZoneId": "America/Los_Angeles"})

    assert LocationHelper.get_timezone_id("San Jose, CA") == "America/Los_Angeles"

    request = _requests_to(requests_mock, TIMEZONE_URL)[0]
    assert _qs(request, "location") == "37.3382,-121.8863"
    assert _qs(request, "timestamp") == "0"
    assert _qs(request, "sensor") == "false"
    assert _qs(request, "key") is None


def test_get_timezone_id_from_lat_lng_with_key(requests_mock: Mocker) -> None:
    _put_google_secrets("sitevar-key")
    requests_mock.get(TIMEZONE_URL, json={"timeZoneId": "Europe/Paris"})

    assert (
        LocationHelper.get_timezone_id("ignored", lat_lng=LatLng(48.85, 2.35))
        == "Europe/Paris"
    )

    assert _requests_to(requests_mock, GEOCODE_URL) == []
    request = _requests_to(requests_mock, TIMEZONE_URL)[0]
    assert _qs(request, "location") == "48.85,2.35"
    assert _qs(request, "key") == "sitevar-key"


def test_get_timezone_id_request_exception(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    requests_mock.get(TIMEZONE_URL, exc=requests.exceptions.ConnectionError)

    assert LocationHelper.get_timezone_id(None, lat_lng=SAN_JOSE) is None
    assert "urlfetch for timezone request failed" in caplog.text


def test_get_timezone_id_http_error(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    requests_mock.get(TIMEZONE_URL, status_code=500)

    assert LocationHelper.get_timezone_id(None, lat_lng=SAN_JOSE) is None
    assert "TZ lookup for (lat, lng) failed! (37.3382, -121.8863)" in caplog.text


def test_get_timezone_id_missing_time_zone_id(
    requests_mock: Mocker, caplog: pytest.LogCaptureFixture
) -> None:
    requests_mock.get(TIMEZONE_URL, json={"status": "ZERO_RESULTS"})

    assert LocationHelper.get_timezone_id(None, lat_lng=SAN_JOSE) is None
    assert "No timeZoneId for (37.3382, -121.8863)" in caplog.text
