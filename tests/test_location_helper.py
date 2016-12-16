import json
import os
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

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
        test_google_api_key = os.environ.get('TEST_GOOGLE_API_KEY', '')
        if not test_google_api_key:
            with open('test_keys.json') as data_file:
                test_keys = json.load(data_file)
                test_google_api_key = test_keys.get('test_google_api_key', '')

        Sitevar(
            id='google.secrets',
            values_json=json.dumps({'api_key': test_google_api_key})).put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_team_location(self):
        # Needs to be loaded after memcache_stub
        from helpers.location_helper import LocationHelper

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
