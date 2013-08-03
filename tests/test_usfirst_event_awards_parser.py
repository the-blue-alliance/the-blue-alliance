import unittest2

from datafeeds.usfirst_event_awards_parser import UsfirstEventAwardsParser

class TestUsfirstEventAwardsParser(unittest2.TestCase):
    def test_parse_regional_2007(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2007sj.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        self.assertEqual(len(awards), 26)
        
        # Test Team Award
        self.assertEqual(awards[25]['official_name'], "Regional Chairman's Award")
        self.assertEqual(awards[25]['team_number'], 604)
        self.assertEqual(awards[25]['awardee'], None)
        self.assertEqual(awards[25]['name'], 'ca')

        # Test Individual Award
        self.assertEqual(awards[7]['official_name'], "Woodie Flowers Award")
        self.assertEqual(awards[7]['team_number'], None)
        self.assertEqual(awards[7]['awardee'], u"Yang Xie \u2013 Team 846")
        self.assertEqual(awards[7]['name'], 'wfa')
        
    def test_parse_regional_2010(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2010sac.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        self.assertEqual(len(awards), 29)

        # Test Team Award
        self.assertEqual(awards[28]['official_name'], "Regional Chairman's Award")
        self.assertEqual(awards[28]['team_number'], 604)
        self.assertEqual(awards[28]['awardee'], None)
        self.assertEqual(awards[28]['name'], 'ca')

        # Test Individual Award
        self.assertEqual(awards[0]['official_name'], "Outstanding Volunteer of the Year")
        self.assertEqual(awards[0]['team_number'], None)
        self.assertEqual(awards[0]['awardee'], "Gary Blakesley")
        self.assertEqual(awards[0]['name'], 'vol')

        # Test Team and Individual Award
        self.assertEqual(awards[8]['official_name'], "Woodie Flowers Award")
        self.assertEqual(awards[8]['team_number'], 604)
        self.assertEqual(awards[8]['awardee'], "Helen Arrington")
        self.assertEqual(awards[8]['name'], 'wfa')

    def test_parse_regional_2012(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2012sj.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())
            
        # Check number of parsed awards
        self.assertEqual(len(awards), 28)
        # Test Team Award
        self.assertEqual(awards[0]['official_name'], "Regional Chairman's Award")
        self.assertEqual(awards[0]['team_number'], 604)
        self.assertEqual(awards[0]['awardee'], None)
        self.assertEqual(awards[0]['name'], 'ca')

        # Test Individual Award
        self.assertEqual(awards[24]['official_name'], "Volunteer of the Year")
        self.assertEqual(awards[24]['team_number'], None)
        self.assertEqual(awards[24]['awardee'], "Joanne Heberer")
        self.assertEqual(awards[24]['name'], 'vol')
        
        # Test Team and Individual Award
        self.assertEqual(awards[26]['official_name'], "Woodie Flowers Finalist Award")
        self.assertEqual(awards[26]['team_number'], 604)
        self.assertEqual(awards[26]['awardee'], "Jim Mori")
        self.assertEqual(awards[26]['name'], 'wfa')

    def test_parse_district_championship_2009(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2009gl.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())
            
        # Check number of parsed awards
        self.assertEqual(len(awards), 30)
        
        # Test Team Award
        self.assertEqual(awards[29]['official_name'], "State Championship Chairman's Award")
        self.assertEqual(awards[29]['team_number'], 217)
        self.assertEqual(awards[29]['awardee'], None)
        self.assertEqual(awards[29]['name'], 'ca2')
        
        self.assertEqual(awards[28]['official_name'], "State Championship Chairman's Award")
        self.assertEqual(awards[28]['team_number'], 33)
        self.assertEqual(awards[28]['awardee'], None)
        self.assertEqual(awards[28]['name'], 'ca1')


        self.assertEqual(awards[27]['official_name'], "State Championship Chairman's Award")
        self.assertEqual(awards[27]['team_number'], 27)
        self.assertEqual(awards[27]['awardee'], None)
        self.assertEqual(awards[27]['name'], 'ca')

        # Test Individual Award
        self.assertEqual(awards[7]['official_name'], "Woodie Flowers Award")
        self.assertEqual(awards[7]['team_number'], None)
        self.assertEqual(awards[7]['awardee'], "Jennifer Harvey of Team 503")
        self.assertEqual(awards[7]['name'], 'wfa')

    def test_parse_district_championship_2012(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2012gl.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())
            
        # Check number of parsed awards
        self.assertEqual(len(awards), 34)
        
        # Test Team Award
        self.assertEqual(awards[0]['official_name'], "Regional Chairman's Award")
        self.assertEqual(awards[0]['team_number'], 33)
        self.assertEqual(awards[0]['awardee'], None)
        self.assertEqual(awards[0]['name'], 'ca')
        
        self.assertEqual(awards[1]['official_name'], "Regional Chairman's Award")
        self.assertEqual(awards[1]['team_number'], 503)
        self.assertEqual(awards[1]['awardee'], None)
        self.assertEqual(awards[1]['name'], 'ca1')


        self.assertEqual(awards[2]['official_name'], "Regional Chairman's Award")
        self.assertEqual(awards[2]['team_number'], 27)
        self.assertEqual(awards[2]['awardee'], None)
        self.assertEqual(awards[2]['name'], 'ca2')

        # Test Team and Individual Award
        self.assertEqual(awards[3]['official_name'], "FIRST Dean's List Finalist Award #1")
        self.assertEqual(awards[3]['team_number'], 3538)
        self.assertEqual(awards[3]['awardee'], 'Jaris Dingman')
        self.assertEqual(awards[3]['name'], 'dl')
        
        self.assertEqual(awards[8]['official_name'], "FIRST Dean's List Finalist Award #6")
        self.assertEqual(awards[8]['team_number'], 1684)
        self.assertEqual(awards[8]['awardee'], 'Matthew Wagner')
        self.assertEqual(awards[8]['name'], 'dl5')
        
    def test_parse_championship_divison_2007(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2007galileo.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())
            
        # Check number of parsed awards
        self.assertEqual(len(awards), 7)
        
        # Test Team Award
        self.assertEqual(awards[0]['official_name'], "Galileo - Highest Rookie Seed")
        self.assertEqual(awards[0]['team_number'], 2272)
        self.assertEqual(awards[0]['awardee'], None)
        self.assertEqual(awards[0]['name'], 'div_hrs')

        self.assertEqual(awards[6]['official_name'], "Galileo - Division Winner #3")
        self.assertEqual(awards[6]['team_number'], 1902)
        self.assertEqual(awards[6]['awardee'], None)
        self.assertEqual(awards[6]['name'], 'div_win3')
        
    def test_parse_championship_2007(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2007cmp.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())
            
        # Check number of parsed awards
        self.assertEqual(len(awards), 29)
        
        # Test Team Award
        self.assertEqual(awards[28]['official_name'], "Championship - Chairman's Award")
        self.assertEqual(awards[28]['team_number'], 365)
        self.assertEqual(awards[28]['awardee'], None)
        self.assertEqual(awards[28]['name'], 'cmp_ca')

        # Test Individual Award
        self.assertEqual(awards[0]['official_name'], "Championship - FRC Outstanding Volunteer Award")
        self.assertEqual(awards[0]['team_number'], None)
        self.assertEqual(awards[0]['awardee'], "Mark Koors")
        self.assertEqual(awards[0]['name'], 'cmp_vol')

    def test_parse_championship_divison_2012(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2012galileo.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())
            
        # Check number of parsed awards
        self.assertEqual(len(awards), 7)
        
        # Test Team Award
        self.assertEqual(awards[0]['official_name'], "Championship Division Winners - Galileo #2")
        self.assertEqual(awards[0]['team_number'], 25)
        self.assertEqual(awards[0]['awardee'], None)
        self.assertEqual(awards[0]['name'], 'div_win2')

        self.assertEqual(awards[6]['official_name'], "Highest Rookie Seed - Galileo")
        self.assertEqual(awards[6]['team_number'], 4394)
        self.assertEqual(awards[6]['awardee'], None)
        self.assertEqual(awards[6]['name'], 'div_hrs')
        
    def test_parse_championship_2012(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2012cmp.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        self.assertEqual(len(awards), 39)
        
        # Test Team Award
        self.assertEqual(awards[0]['official_name'], "Chairman's Award")
        self.assertEqual(awards[0]['team_number'], 1114)
        self.assertEqual(awards[0]['awardee'], None)
        self.assertEqual(awards[0]['name'], 'cmp_ca')

        # Test Individual Award
        self.assertEqual(awards[1]['official_name'], "Founder's Award")
        self.assertEqual(awards[1]['team_number'], None)
        self.assertEqual(awards[1]['awardee'], "Google")
        self.assertEqual(awards[1]['name'], 'cmp_founders')

        # Test Team and Individual Award
        self.assertEqual(awards[15]['official_name'], "FIRST Dean's List Award #2")
        self.assertEqual(awards[15]['team_number'], 1540)
        self.assertEqual(awards[15]['awardee'], "Marina Dimitrov")
        self.assertEqual(awards[15]['name'], 'cmp_dl1')
        
        self.assertEqual(awards[36]['official_name'], "Woodie Flowers Award")
        self.assertEqual(awards[36]['team_number'], 2614)
        self.assertEqual(awards[36]['awardee'], "Earl Scime")
        self.assertEqual(awards[36]['name'], 'cmp_wfa')
        
    def test_parse_championship_2013(self):
        with open('test_data/usfirst_html/usfirst_event_awards_2013cmp.html', 'r') as f:
            awards, _ = UsfirstEventAwardsParser.parse(f.read())

        # Check number of parsed awards
        self.assertEqual(len(awards), 37)
        
        # Test New Awards
        self.assertEqual(awards[20]['official_name'], 'Make It Loud Award')
        self.assertEqual(awards[20]['team_number'], None)
        self.assertEqual(awards[20]['awardee'], 'will.i.am')
        self.assertEqual(awards[20]['name'], 'cmp_mil')
        
        self.assertEqual(awards[28]['official_name'], 'Media and Technology Award sponsored by Comcast')
        self.assertEqual(awards[28]['team_number'], 2283)
        self.assertEqual(awards[28]['awardee'], None)
        self.assertEqual(awards[28]['name'], 'cmp_mediatech')

        self.assertEqual(awards[35]['official_name'], 'Dr. Bart Kamen Memorial Scholarship #2')
        self.assertEqual(awards[35]['team_number'], None)
        self.assertEqual(awards[35]['awardee'], 'Sarah Rudasill')
        self.assertEqual(awards[35]['name'], 'cmp_bkm2')
