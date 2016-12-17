import json
import os
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.location_helper import LocationHelper
from models.event import Event
from models.sitevar import Sitevar
from models.team import Team


class TestLocationHelper(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        # Load env vars that contain test keys
        test_google_api_key = os.environ.get('TEST_GOOGLE_API_KEY', '')  # Frome in Travis CI
        if not test_google_api_key:
            with open('test_keys.json') as data_file:
                test_keys = json.load(data_file)
                test_google_api_key = test_keys.get('test_google_api_key', '')

        Sitevar(
            id='google.secrets',
            values_json=json.dumps({'api_key': test_google_api_key})).put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_event_location(self):
        # 2016cama (weird venue)
        event = Event(
            id='2016cama',
            city='Madera',
            state_prov='CA',
            country='USA',
            postalcode='93637',
            venue='Madera South High School',
            venue_address='Madera South High School\n705 W. Pecan Avenue\nMadera, CA 93637\nUSA'
            )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, 'Madera South High School')
        self.assertEqual(event.normalized_location.formatted_address, '705 W Pecan Ave, Madera, CA 93637, United States')
        self.assertEqual(event.normalized_location.street_number, '705')
        self.assertEqual(event.normalized_location.street, 'West Pecan Avenue')
        self.assertEqual(event.normalized_location.city, 'Madera')
        self.assertEqual(event.normalized_location.state_prov, 'California')
        self.assertEqual(event.normalized_location.state_prov_short,  'CA')
        self.assertEqual(event.normalized_location.country, 'United States')
        self.assertEqual(event.normalized_location.country_short, 'US')
        self.assertEqual(event.normalized_location.postal_code, '93637')
        self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(36.9393999, -120.0664811))

        # 2016cada (weird address)
        event = Event(
            id='2016cada',
            city='Davis',
            state_prov='CA',
            country='USA',
            postalcode='95616',
            venue='UC Davis ARC Pavilion',
            venue_address='UC Davis ARC Pavilion\nCorner of Orchard and LaRue\nDavis, CA 95616\nUSA'
            )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, 'The Pavilion')
        self.assertEqual(event.normalized_location.formatted_address, 'Davis, CA 95616, United States')
        self.assertEqual(event.normalized_location.street_number, None)
        self.assertEqual(event.normalized_location.street, None)
        self.assertEqual(event.normalized_location.city, 'Davis')
        self.assertEqual(event.normalized_location.state_prov, 'California')
        self.assertEqual(event.normalized_location.state_prov_short,  'CA')
        self.assertEqual(event.normalized_location.country, 'United States')
        self.assertEqual(event.normalized_location.country_short, 'US')
        self.assertEqual(event.normalized_location.postal_code, '95616')
        self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(38.5418888, -121.7595864))

        # 2016casj (weird venue)
        event = Event(
            id='2016casj',
            city='San Jose',
            state_prov='CA',
            country='USA',
            postalcode='95112',
            venue='San Jose State University - The Event Center',
            venue_address='San Jose State University - The Event Center\n290 South 7th Street\nSan Jose, CA 95112\nUSA'
            )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, 'The Event Center at SJSU')
        self.assertEqual(event.normalized_location.formatted_address, '290 S 7th St, San Jose, CA 95112, United States')
        self.assertEqual(event.normalized_location.street_number, '290')
        self.assertEqual(event.normalized_location.street, 'South 7th Street')
        self.assertEqual(event.normalized_location.city, 'San Jose')
        self.assertEqual(event.normalized_location.state_prov, 'California')
        self.assertEqual(event.normalized_location.state_prov_short,  'CA')
        self.assertEqual(event.normalized_location.country, 'United States')
        self.assertEqual(event.normalized_location.country_short, 'US')
        self.assertEqual(event.normalized_location.postal_code, '95112')
        self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(37.33522809999999, -121.8800817))

        # 2016cmp (no venue address)
        event = Event(
            id='2016cmp',
            city='St. Louis',
            state_prov='MO',
            country='USA',
            postalcode='95112',
            venue='The Dome at America\'s Center',
            venue_address=None
            )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, 'The Dome at America\'s Center')
        self.assertEqual(event.normalized_location.formatted_address, '901 N Broadway, St. Louis, MO 63101, United States')
        self.assertEqual(event.normalized_location.street_number, '901')
        self.assertEqual(event.normalized_location.street, 'North Broadway')
        self.assertEqual(event.normalized_location.city, 'St. Louis')
        self.assertEqual(event.normalized_location.state_prov, 'Missouri')
        self.assertEqual(event.normalized_location.state_prov_short,  'MO')
        self.assertEqual(event.normalized_location.country, 'United States')
        self.assertEqual(event.normalized_location.country_short, 'US')
        self.assertEqual(event.normalized_location.postal_code, '63101')
        self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(38.6328287, -90.1885095))

        # 2016ausy (Australia event)
        event = Event(
            id='2016ausy',
            city='Sydney Olympic Park',
            state_prov='NSW',
            country='Australia',
            postalcode='2127',
            venue='Sydney Olympic Park Sports Centre',
            venue_address='Sydney Olympic Park Sports Centre\nOlympic Boulevard\nSydney Olympic Park, NSW 2127\nAustralia'
            )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, 'Sydney Olympic Park Sports Centre')
        self.assertEqual(event.normalized_location.formatted_address, 'Olympic Blvd, Sydney Olympic Park NSW 2127, Australia')
        self.assertEqual(event.normalized_location.street_number, None)
        self.assertEqual(event.normalized_location.street, 'Olympic Boulevard')
        self.assertEqual(event.normalized_location.city, 'Sydney Olympic Park')
        self.assertEqual(event.normalized_location.state_prov, 'New South Wales')
        self.assertEqual(event.normalized_location.state_prov_short,  'NSW')
        self.assertEqual(event.normalized_location.country, 'Australia')
        self.assertEqual(event.normalized_location.country_short, 'AU')
        self.assertEqual(event.normalized_location.postal_code, '2127')
        self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(-33.85341090000001, 151.0693752))

        # # 2016gush (China event with really bad location details)
        # event = Event(
        #     id='2016gush',
        #     city='Shenzhen City',
        #     state_prov='44',
        #     country='China',
        #     postalcode='518000',
        #     venue='The Sports Center of Shenzhen University',
        #     venue_address='The Sports Center of Shenzhen University\nNo. 2032 Liuxian Road\nNanshan District\nShenzhen City, 44 518000\nChina'
        #     )
        # LocationHelper.update_event_location(event)
        # self.assertEqual(event.normalized_location.name, 'Shenzhen University Town Sports Center')
        # self.assertEqual(event.normalized_location.formatted_address, 'Liuxian Ave, Shenzhen, Guangdong, China')
        # self.assertEqual(event.normalized_location.street_number, None)
        # self.assertEqual(event.normalized_location.street, 'Liuxian Avenue')
        # self.assertEqual(event.normalized_location.city, 'Shenzhen Shi')
        # self.assertEqual(event.normalized_location.state_prov, 'Guangdong Sheng')
        # self.assertEqual(event.normalized_location.state_prov_short,  'Guangdong Sheng')
        # self.assertEqual(event.normalized_location.country, 'China')
        # self.assertEqual(event.normalized_location.country_short, 'CN')
        # self.assertEqual(event.normalized_location.postal_code, '518055')
        # self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(22.585279, 113.978825))

        # 2016code
        event = Event(
            id='2016code',
            city='Denver',
            state_prov='CO',
            country='USA',
            postalcode='80210',
            venue=' University of Denver - Daniel L. Ritchie Center',
            venue_address='University of Denver - Daniel L. Ritchie Center\n2201 East Asbury Ave\nDenver, CO 80210\nUSA'
            )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, 'Ritchie Center')
        self.assertEqual(event.normalized_location.formatted_address, '2240 Buchtel Blvd S, Denver, CO 80210, United States')
        self.assertEqual(event.normalized_location.street_number, '2240')
        self.assertEqual(event.normalized_location.street, 'Buchtel Boulevard South')
        self.assertEqual(event.normalized_location.city, 'Denver')
        self.assertEqual(event.normalized_location.state_prov, 'Colorado')
        self.assertEqual(event.normalized_location.state_prov_short,  'CO')
        self.assertEqual(event.normalized_location.country, 'United States')
        self.assertEqual(event.normalized_location.country_short, 'US')
        self.assertEqual(event.normalized_location.postal_code, '80210')
        self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(39.6819652, -104.9618983))

        # 2016ilpe
        event = Event(
            id='2016ilpe',
            city='Peoria',
            state_prov='IL',
            country='USA',
            postalcode='61625',
            venue='Renaissance Coliseum - Bradley University',
            venue_address='Renaissance Coliseum - Bradley University\n1600 W. Main Street\nPeoria, IL 61625\nUSA'
            )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, 'Renaissance Coliseum')
        self.assertEqual(event.normalized_location.formatted_address, 'Renaissance Coliseum, N Maplewood Ave, Peoria, IL 61606, USA')
        self.assertEqual(event.normalized_location.street_number, None)
        self.assertEqual(event.normalized_location.street, 'North Maplewood Avenue')
        self.assertEqual(event.normalized_location.city, 'Peoria')
        self.assertEqual(event.normalized_location.state_prov, 'Illinois')
        self.assertEqual(event.normalized_location.state_prov_short,  'IL')
        self.assertEqual(event.normalized_location.country, 'United States')
        self.assertEqual(event.normalized_location.country_short, 'US')
        self.assertEqual(event.normalized_location.postal_code, '61606')
        self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(40.69919369999999, -89.61780639999999))

        # 2017isde1
        event = Event(
            id='2016ide1',
            city='Haifa',
            state_prov='HA',
            country='Israel',
            postalcode='00000',
            venue='Technion Sports Center',
            venue_address='Technion Sports Center\nTechnion\nHaifa, HA 00000\nIsrael'
            )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, 'Technion Sports Center')
        self.assertEqual(event.normalized_location.formatted_address, 'Derech Ya\'akov Dori, Haifa, Israel')
        self.assertEqual(event.normalized_location.street_number, None)
        self.assertEqual(event.normalized_location.street, 'Derech Ya\'akov Dori')
        self.assertEqual(event.normalized_location.city, 'Haifa')
        self.assertEqual(event.normalized_location.state_prov, 'Haifa District')
        self.assertEqual(event.normalized_location.state_prov_short,  'Haifa District')
        self.assertEqual(event.normalized_location.country, 'Israel')
        self.assertEqual(event.normalized_location.country_short, 'IL')
        self.assertEqual(event.normalized_location.postal_code, None)
        self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(32.77911630000001, 35.01909250000001))

        # 2017isde3
        event = Event(
            id='2016isde3',
            city='Tel-Aviv, Yafo',
            state_prov='TA',
            country='Israel',
            postalcode='00000',
            venue='Shlomo Group Arena',
            venue_address='Shlomo Group Arena\n7 Isaac Remba St\nTel-Aviv, Yafo, TA 00000\nIsrael'
            )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, 'Shlomo Group arena')
        self.assertEqual(event.normalized_location.formatted_address, 'Isaac Remba St 27, Tel Aviv-Yafo, Israel')
        self.assertEqual(event.normalized_location.street_number, '27')
        self.assertEqual(event.normalized_location.street, 'Isaac Remba Street')
        self.assertEqual(event.normalized_location.city, 'Tel Aviv-Yafo')
        self.assertEqual(event.normalized_location.state_prov, 'Tel Aviv District')
        self.assertEqual(event.normalized_location.state_prov_short,  'Tel Aviv District')
        self.assertEqual(event.normalized_location.country, 'Israel')
        self.assertEqual(event.normalized_location.country_short, 'IL')
        self.assertEqual(event.normalized_location.postal_code, None)
        self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(32.1090726,34.8113608))

        # 2017mndu
        event = Event(
            id='2016mndu',
            city='Duluth',
            state_prov='MN',
            country='USA',
            postalcode='55802',
            venue='DECC Arena/South Pioneer Hall',
            venue_address='DECC Arena/South Pioneer Hall\nDuluth Entertainment Convention Center\n350 Harbor Drive\nDuluth, MN 55802\nUSA'
            )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, 'Duluth Entertainment Convention Center')
        self.assertEqual(event.normalized_location.formatted_address, '350 Harbor Dr, Duluth, MN 55802, United States')
        self.assertEqual(event.normalized_location.street_number, '350')
        self.assertEqual(event.normalized_location.street, 'Harbor Drive')
        self.assertEqual(event.normalized_location.city, 'Duluth')
        self.assertEqual(event.normalized_location.state_prov, 'Minnesota')
        self.assertEqual(event.normalized_location.state_prov_short,  'MN')
        self.assertEqual(event.normalized_location.country, 'United States')
        self.assertEqual(event.normalized_location.country_short, 'US')
        self.assertEqual(event.normalized_location.postal_code, '55802')
        self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(46.78126760000001, -92.09950649999999))

        # 2017mxto
        event = Event(
            id='2016mxto',
            city='Torreon',
            state_prov='COA',
            country='Mexico',
            postalcode='27250',
            venue='ITESM Campus Laguna - Santiago Garza de la Mora',
            venue_address='ITESM Campus Laguna - Santiago Garza de la Mora\nPaseo del Tecnologico #751\nTorreon, COA 27250\nMexico'
            )
        LocationHelper.update_event_location(event)
        self.assertEqual(event.normalized_location.name, u'Instituto Tecnol\xf3gico de Estudios Superiores de Monterrey')
        self.assertEqual(event.normalized_location.formatted_address, u'Paseo del Tecnol\xf3gico 751, Amp la Rosita, 27250 Torre\xf3n, Coah., Mexico')
        self.assertEqual(event.normalized_location.street_number, None)
        self.assertEqual(event.normalized_location.street, None)
        self.assertEqual(event.normalized_location.city, u'Torre\xf3n')
        self.assertEqual(event.normalized_location.state_prov, 'Coahuila de Zaragoza')
        self.assertEqual(event.normalized_location.state_prov_short,  'Coah.')
        self.assertEqual(event.normalized_location.country, 'Mexico')
        self.assertEqual(event.normalized_location.country_short, 'MX')
        self.assertEqual(event.normalized_location.postal_code, '27250')
        self.assertEqual(event.normalized_location.lat_lng, ndb.GeoPt(25.5173546, -103.3976534))

    def test_team_location(self):
        # Team 604 (generic team)
        team = Team(
            id='frc604',
            name='Brin Wojcicki Foundation/IBM/Google.org/Qualcomm/Apple/Team Grandma/BAE Systems/Western Digital/WAGIC/Lockheed Martin/TE connectivity/Leland Bridge/Intuitive Surgical/San Jose City Councilman J. Khamis/eBay/Cisco/Dell/MDR Precision/ Benevity /SOLIDWORKS/Sierra Radio Systems/HSC Electronic Supply/Hurricane Electric/Dropbox/STL Shipping by FRC3256/GitHub & Leland High',
            city='San Jose',
            state_prov='California',
            postalcode='95120',
            country='USA'
            )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, 'Leland High School')
        self.assertEqual(team.normalized_location.formatted_address, '6677 Camden Avenue, San Jose, CA 95120, United States')
        self.assertEqual(team.normalized_location.street_number, '6677')
        self.assertEqual(team.normalized_location.street, 'Camden Avenue')
        self.assertEqual(team.normalized_location.city, 'San Jose')
        self.assertEqual(team.normalized_location.state_prov, 'California')
        self.assertEqual(team.normalized_location.state_prov_short, 'CA')
        self.assertEqual(team.normalized_location.country, 'United States')
        self.assertEqual(team.normalized_location.country_short, 'US')
        self.assertEqual(team.normalized_location.postal_code, '95120')
        self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(37.217065, -121.842901))

        # Team 1868 (Odd Sponsors, multiple schools)
        team = Team(
            id='frc1868',
            name='NASA Ames Research Center / St. Jude Medical Foundation / Google / Nvidia / Brin Worcicki Foundation / Qualcomm / Intuitive Surgical / Motorola / World Metal Finishing / Applied Welding / Weiss Enterprises / Solidworks / Wildbit / Fiber Internet Center & Girl Scout Troop 62868',
            city='Mountain View',
            state_prov='California',
            postalcode='94035',
            country='USA'
            )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, 'NASA Ames Research Center')
        self.assertEqual(team.normalized_location.formatted_address, 'MOFFETT FIELD, CA 94035, United States')
        self.assertEqual(team.normalized_location.street_number, None)
        self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, 'MOFFETT FIELD')
        self.assertEqual(team.normalized_location.state_prov, 'California')
        self.assertEqual(team.normalized_location.state_prov_short, 'CA')
        self.assertEqual(team.normalized_location.country, 'United States')
        self.assertEqual(team.normalized_location.country_short, 'US')
        self.assertEqual(team.normalized_location.postal_code, '94035')
        self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(37.4090697, -122.0638253))

        # Team 3504 (Odd Sponsors, multiple schools)
        team = Team(
            id='frc3504',
            name='Field Robotics Center, Carnegie Mellon University / American Eagle Outfitters & Fox Chapel Area Hs & Oakland Catholic High School & Pittsburgh Brashear Hs & Pittsburgh Science and Technology Academy 6-12 & Avonworth Hs & Pittsburgh Capa 6-12 & Bishop Canevin High School & Dorseyville Ms & Plum Shs & Winchester Thurston School & North Allegheny Shs & North Allegheny Ihs & Pine-Richland Hs & Seneca Valley Shs & Upper Saint Clair Hs & The Ellis School & PA Cyber Charter School & Aquinas Academy & Penn Hills Shs & Harrold Middle School & Sacred Heart Elementary School & Pittsburgh Obama 6-12 & Hampton Middle School & Hampton Hs & Franklin Regional Ms & Canon-Mcmillan Shs & South Fayette Ms & Community College Allegheny County & Home School & Home School & Home School',
            city='Pittsburgh',
            state_prov='Pennsylvania',
            postalcode='15213',
            country='USA'
            )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, 'Carnegie Mellon University Field Robotics Center')
        self.assertEqual(team.normalized_location.formatted_address, 'Pittsburgh, PA 15213, United States')
        self.assertEqual(team.normalized_location.street_number, None)
        self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, 'Pittsburgh')
        self.assertEqual(team.normalized_location.state_prov, 'Pennsylvania')
        self.assertEqual(team.normalized_location.state_prov_short, 'PA')
        self.assertEqual(team.normalized_location.country, 'United States')
        self.assertEqual(team.normalized_location.country_short, 'US')
        self.assertEqual(team.normalized_location.postal_code, '15213')
        self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(40.4433142, -79.9452154))

        # Team 67 (Multiple schools)
        team = Team(
            id='frc67',
            name='General Motors Milford Proving Ground & Huron Valley Schools',
            city='Highland',
            state_prov='Michigan',
            postalcode='48357',
            country='USA'
            )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, 'Huron Valley Schools')
        self.assertEqual(team.normalized_location.formatted_address, '2390 S Milford Rd, Highland, MI 48357, United States')
        self.assertEqual(team.normalized_location.street_number, '2390')
        self.assertEqual(team.normalized_location.street, 'South Milford Road')
        self.assertEqual(team.normalized_location.city, 'Highland Charter Township')
        self.assertEqual(team.normalized_location.state_prov, 'Michigan')
        self.assertEqual(team.normalized_location.state_prov_short, 'MI')
        self.assertEqual(team.normalized_location.country, 'United States')
        self.assertEqual(team.normalized_location.country_short, 'US')
        self.assertEqual(team.normalized_location.postal_code, '48357')
        self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(42.6171756, -83.6182952))

        # Team 6018 (School in China)
        team = Team(
            id='frc6018',
            name='High School Attached to Northwestern Normal University',
            city='Lanzhou',
            state_prov='Gansu',
            postalcode='730070',
            country='China'
            )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, 'High School Attached To Northwest Normal University')
        self.assertEqual(team.normalized_location.formatted_address, '21 Shilidian S St, Anning, Lanzhou, Gansu, China')
        self.assertEqual(team.normalized_location.street_number, '21')
        self.assertEqual(team.normalized_location.street, 'Shilidian South Street')
        self.assertEqual(team.normalized_location.city, 'Lanzhou Shi')
        self.assertEqual(team.normalized_location.state_prov, 'Gansu Sheng')
        self.assertEqual(team.normalized_location.state_prov_short, 'Gansu Sheng')
        self.assertEqual(team.normalized_location.country, 'China')
        self.assertEqual(team.normalized_location.country_short, 'CN')
        self.assertEqual(team.normalized_location.postal_code, '730070')
        self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(36.09318959999999, 103.7491115))

        # Team 6434 (School in Australia)
        team = Team(
            id='frc6434',
            name='Bossley Park High School',
            city='Bossley Park',
            state_prov='New South Wales',
            postalcode='2176',
            country='Australia'
            )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, 'Bossley Park High School')
        self.assertEqual(team.normalized_location.formatted_address, '36-44 Prairie Vale Rd, Bossley Park NSW 2176, Australia')
        self.assertEqual(team.normalized_location.street_number, '36-44')
        self.assertEqual(team.normalized_location.street, 'Prairie Vale Road')
        self.assertEqual(team.normalized_location.city, 'Bossley Park')
        self.assertEqual(team.normalized_location.state_prov, 'New South Wales')
        self.assertEqual(team.normalized_location.state_prov_short, 'NSW')
        self.assertEqual(team.normalized_location.country, 'Australia')
        self.assertEqual(team.normalized_location.country_short, 'AU')
        self.assertEqual(team.normalized_location.postal_code, '2176')
        self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(-33.870024, 150.8753854))

        # Team 2122 (Complicated team name, wrong postal code)
        team = Team(
            id='frc2122',
            name='Micron Technology, Inc./Hewlett Packard/Boise Schools Educational Foundation/Laura Moore Cunningham Foundation/J.C. Jeker Foundation & Treasure Valley Math/Science',
            city='Boise',
            state_prov='Idaho',
            postalcode='83709',
            country='USA'
            )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, 'TVMSC')
        self.assertEqual(team.normalized_location.formatted_address, '6801 N Gary Ln, Boise, ID 83714, United States')
        self.assertEqual(team.normalized_location.street_number, '6801')
        self.assertEqual(team.normalized_location.street, 'North Gary Lane')
        self.assertEqual(team.normalized_location.city, 'Boise')
        self.assertEqual(team.normalized_location.state_prov, 'Idaho')
        self.assertEqual(team.normalized_location.state_prov_short, 'ID')
        self.assertEqual(team.normalized_location.country, 'United States')
        self.assertEqual(team.normalized_location.country_short, 'US')
        self.assertEqual(team.normalized_location.postal_code, '83714')
        self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(43.68010509999999, -116.2800371))

        # Team 3354 (Mexican team, special symbols, odd school name)
        team = Team(
            id='frc3354',
            name='Mabe/Bombardier Aerospace Mexico/Coca Cola/Grupo Salinas/Fundacion Azteca/Navex/Red Cross/United Nations/Lego Education/Foundation For a Drug Free World & Tec de Monterrey',
            city='Queretaro',
            state_prov=u'Quer\xe9taro',
            postalcode='76130',
            country='Mexico'
            )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, u'Tecnol\xf3gico de Monterrey')
        self.assertEqual(team.normalized_location.formatted_address, u'Epigmenio Gonz\xe1lez 500, San Pablo, 76130 Santiago de Quer\xe9taro, Qro., Mexico')
        self.assertEqual(team.normalized_location.street_number, '500')
        self.assertEqual(team.normalized_location.street, u'Epigmenio Gonz\xe1lez')
        self.assertEqual(team.normalized_location.city, u'Santiago de Quer\xe9taro')
        self.assertEqual(team.normalized_location.state_prov, u'Quer\xe9taro')
        self.assertEqual(team.normalized_location.state_prov_short, 'Qro.')
        self.assertEqual(team.normalized_location.country, 'Mexico')
        self.assertEqual(team.normalized_location.country_short, 'MX')
        self.assertEqual(team.normalized_location.postal_code, '76130')
        self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(20.6133432, -100.4053132))

        # Team 3933 (Mexican team, special symbols, odd school name)
        team = Team(
            id='frc3933',
            name=u'General Motors Mexico & Tecnol\xe1gico de Monterrey Campus Santa Fe',
            city='Mexico',
            state_prov='Distrito Federal',
            postalcode='01389',
            country='Mexico'
            )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, 'Tec de Monterrey Campus Santa Fe (ITESM)')
        self.assertEqual(team.normalized_location.formatted_address, u'Av. Carlos Lazo #100, \xc1lvaro Obreg\xf3n, Santa Fe, 01389 Ciudad de M\xe9xico, CDMX, Mexico')
        self.assertEqual(team.normalized_location.street_number, None)
        self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, u'Ciudad de M\xe9xico')
        self.assertEqual(team.normalized_location.state_prov, u'Ciudad de M\xe9xico')
        self.assertEqual(team.normalized_location.state_prov_short, 'CDMX')
        self.assertEqual(team.normalized_location.country, 'Mexico')
        self.assertEqual(team.normalized_location.country_short, 'MX')
        self.assertEqual(team.normalized_location.postal_code, '01389')
        self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(19.3593887, -99.26045889999999))

        # Team 6227 (Chinese team, odd school name)
        team = Team(
            id='frc6227',
            name='The Middle School Attached to Northwestern Polytechnical University / ROBOTERRA & Family Friends',
            city='Xi\'An',
            state_prov='Shaanxi',
            postalcode=None,
            country='China'
            )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, 'Northwestern Polytechnical University Affiliated Middle School')
        self.assertEqual(team.normalized_location.formatted_address, '127 Youyi W Rd, Beilin, Xi\'an, Shaanxi, China')
        self.assertEqual(team.normalized_location.street_number, u'127\u53f7')
        self.assertEqual(team.normalized_location.street, 'Youyi West Road')
        self.assertEqual(team.normalized_location.city, 'Xian Shi')
        self.assertEqual(team.normalized_location.state_prov, 'Shaanxi Sheng')
        self.assertEqual(team.normalized_location.state_prov_short, 'Shaanxi Sheng')
        self.assertEqual(team.normalized_location.country, 'China')
        self.assertEqual(team.normalized_location.country_short, 'CN')
        self.assertEqual(team.normalized_location.postal_code, '710000')
        self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(34.24073449999999, 108.916593))

        # Team 6228 (Turkish team, odd school name)
        team = Team(
            id='frc6228',
            name='Ministry of Education/Odeabank/Arena Advertising/Trio Machine/Turkish Airlines/Metalinoks/Sisli Municipality/Hisim Group/Fikret Yuksel Foundation/Metal Yapi & Macka Akif Tuncel Vocational and Technical High School',
            city='Istanbul',
            state_prov='Istanbul',
            postalcode='34367',
            country='Turkey'
            )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, u'Ma\xe7ka Akif Tuncel Mesleki ve Teknik Anadolu Lisesi')
        self.assertEqual(team.normalized_location.formatted_address, u'Harbiye Mh., Ma\xe7ka Caddesi No10, 34367 \u015ei\u015fli/\u0130stanbul, Turkey')
        self.assertEqual(team.normalized_location.street_number, None)
        self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, u'\u0130stanbul')
        self.assertEqual(team.normalized_location.state_prov, u'\u0130stanbul')
        self.assertEqual(team.normalized_location.state_prov_short, u'\u0130stanbul')
        self.assertEqual(team.normalized_location.country, 'Turkey')
        self.assertEqual(team.normalized_location.country_short, 'TR')
        self.assertEqual(team.normalized_location.postal_code, '34367')
        self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(41.047045, 28.994531))

        # Team 6231 (Turkish team, odd school name)
        team = Team(
            id='frc6231',
            name=u'Haydar Ak\u0131n Mesleki Teknik Anadolu L\u0131ses\u0131 & Immib Bahcelievler Erkan Avci Mesleki ve Teknik Anadolu Lisesi',
            city='Istanbul',
            state_prov='Istanbul',
            postalcode=None,
            country='Turkey'
            )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, u'\u0130MM\u0130B Erkan Avc\u0131 Mesleki ve Teknik Anadolu Lisesi')
        self.assertEqual(team.normalized_location.formatted_address, u'Bah\xe7elievler, K\xfclt\xfcr Sk. No:3, . K\xfclt\xfcr Sk. Bah\xe7elievler/\u0130stanbul, Turkey')
        self.assertEqual(team.normalized_location.street_number, '3')
        self.assertEqual(team.normalized_location.street, u'K\xfclt\xfcr Sokak')
        self.assertEqual(team.normalized_location.city, u'\u0130stanbul')
        self.assertEqual(team.normalized_location.state_prov, u'\u0130stanbul')
        self.assertEqual(team.normalized_location.state_prov_short, u'\u0130stanbul')
        self.assertEqual(team.normalized_location.country, 'Turkey')
        self.assertEqual(team.normalized_location.country_short, 'TR')
        self.assertEqual(team.normalized_location.postal_code, u'. K\xfclt\xfcr Sk.')
        self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(40.996236, 28.8618779))

        # Team 4403 (Turkish team, odd school name)
        team = Team(
            id='frc4403',
            name=u'MET MEX PE\xd1OLES, S.A. DE C.V. & Tec de Monterrey Campus Laguna',
            city='Torreon',
            state_prov='Coahuila',
            postalcode='27250',
            country='Mexico'
            )
        LocationHelper.update_team_location(team)
        self.assertEqual(team.normalized_location.name, u'Instituto Tecnol\xf3gico de Estudios Superiores de Monterrey')
        self.assertEqual(team.normalized_location.formatted_address, u'Paseo del Tecnol\xf3gico 751, Amp la Rosita, 27250 Torre\xf3n, Coah., Mexico')
        self.assertEqual(team.normalized_location.street_number, None)
        self.assertEqual(team.normalized_location.street, None)
        self.assertEqual(team.normalized_location.city, u'Torre\xf3n')
        self.assertEqual(team.normalized_location.state_prov, 'Coahuila de Zaragoza')
        self.assertEqual(team.normalized_location.state_prov_short, 'Coah.')
        self.assertEqual(team.normalized_location.country, 'Mexico')
        self.assertEqual(team.normalized_location.country_short, 'MX')
        self.assertEqual(team.normalized_location.postal_code, '27250')
        self.assertEqual(team.normalized_location.lat_lng, ndb.GeoPt(25.5173546, -103.3976534))
