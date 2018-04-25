from models.district import District


class FMSAPIDistrictRankingsParser(object):

    def __init__(self, advancement):
        self.advancement = advancement

    def parse(self, response):
        current_page = response['pageCurrent']
        total_pages = response['pageTotal']
        models = []

        team_advancement = {
            'frc{}'.format(r['teamNumber']): {
                'dcmp': r['qualifiedDistrictCmp'],
                'cmp': r['qualifiedFirstCmp']
            } for r in response['districtRanks']
        }
        self.advancement.update(team_advancement)
        return (self.advancement, (current_page < total_pages))
