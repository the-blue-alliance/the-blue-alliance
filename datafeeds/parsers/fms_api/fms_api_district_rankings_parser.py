from models.district import District


class FMSAPIDistrictRankingsParser(object):

    def __init__(self, rankings):
        self.rankings = rankings

    def parse(self, response):
        current_page = response['pageCurrent']
        total_pages = response['pageTotal']
        models = []

        self.rankings.extend(response['districtRanks'])
        return (self.rankings, (current_page < total_pages))
