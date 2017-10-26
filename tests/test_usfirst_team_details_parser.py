import unittest2

from datafeeds.usfirst_team_details_parser import UsfirstTeamDetailsParser


@unittest2.skip
class TestUsfirstTeamDetailsParser(unittest2.TestCase):
    def test_parse_team_not_found(self):
        with open('test_data/usfirst_html/usfirst_team_details_team_not_found.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team, None)

    def test_parse_frc254_2014(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc254_2014.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team["address"], u"San Jose, CA, USA")
        self.assertEqual(team["name"], "NASA Ames Research Center / Lockheed Martin / The Mercadante Family / Ooyala / TR Manufacturing / Qualcomm / HP / West Coast Products / The Magarelli Family / The Yun Family / Google / Modern Machine / The Gebhart Family / Aditazz / Cisco Meraki / Vivid-Hosting / Nvidia / BAE Systems / Gilbert Spray Coat / Pacific Coast Metal / S&S Welding / Good Plastics / Team Whyachi / Hy-Tech Plating / Applied Welding / World Metal Finishing / The Jimenez Family & Bellarmine College Preparatory")
        self.assertEqual(team["nickname"], "The Cheesy Poofs")
        self.assertEqual(team["team_number"], 254)
        self.assertEqual(team["website"], "http://www.team254.com")

    def test_parse_frc842_2014(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc842_2014.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team["address"], u"Phoenix, AZ, USA")
        self.assertEqual(team["name"], "The Boeing Company/DLR Group/Fast Signs/Southwest Fasteners & Carl Hayden High School")
        self.assertEqual(team["nickname"], "Falcon Robotics")
        self.assertEqual(team["team_number"], 842)
        self.assertEqual(team["website"], "https://sites.google.com/site/falconroboticsfrcteam842/frc-robots/2014-dream")

    def test_parse_frc999_2014(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc999_2014.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team["address"], u"Cheshire, CT, USA")
        self.assertEqual(team["name"], "Sikorsky Aircraft & Cheshire High School")
        self.assertEqual(team["nickname"], "MechaRams (Cheshire Robotics and Sikorsky Helicopters)")
        self.assertEqual(team["team_number"], 999)
        self.assertEqual(team["website"], "https://sites.google.com/a/cheshire.k12.ct.us/crash999")

    def test_parse_frc177_2013(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc177_2013.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team["address"], u"South Windsor, CT, USA")
        self.assertEqual(team["name"], "UTC Power/Ensign Bickford Aerospace & Defense & South Windsor High School")
        self.assertEqual(team["nickname"], "Bobcat Robotics")
        self.assertEqual(team["team_number"], 177)
        self.assertEqual(team["website"], "http://www.bobcatrobotics.org")

    def test_parse_frc1114_2013(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc1114_2013.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team["address"], u"St. Catharines, ON, Canada")
        self.assertEqual(team["name"], "Innovation First International/General Motors St. Catharines Powertrain & Simbotics")
        self.assertEqual(team["nickname"], "Simbotics")
        self.assertEqual(team["team_number"], 1114)
        self.assertEqual(team["website"], "http://www.simbotics.org")

    def test_parse_frc4590_2013(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc4590_2013.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team["address"], u"Kfar Hayarok, TA, Israel")
        self.assertEqual(team["name"], "Hakfar Hayarok")
        self.assertEqual(team["nickname"], "Greenblitz")
        self.assertEqual(team["team_number"], 4590)

    def test_parse_frc4756_2013(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc4756_2013.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team["name"], "aaaaaa")
        self.assertEqual(team["nickname"], "wgogfom3")
        self.assertEqual(team["team_number"], 4756)

    def test_parse_frc1309_2004(self):
        with open('test_data/usfirst_html/usfirst_team_details_frc1309_2004.html', 'r') as f:
            team, _ = UsfirstTeamDetailsParser.parse(f.read())

        self.assertEqual(team["address"], u"Toronto, ON, Canada")
        self.assertEqual(team["name"], "Toronto District School Board & Emery Collegiate Institute")
        self.assertEqual(team["nickname"], "Diamond Eagles")
        self.assertEqual(team["team_number"], 1309)
