class FMSAPIEventRankingsParser(object):
    def __init__(self, year):
        self.year = year

    def parse(self, response):
        parsers = {
            2015: self.parse2015,
            2016: self.parse2016,
        }
        return parsers[self.year](response)

    def parse2015(self, response):
        rankings = [['Rank', 'Team', 'Qual Avg', 'Auto', 'Container', 'Coopertition', 'Litter', 'Tote', 'Played']]

        for team in response['Rankings']:
            rankings.append([
                team['rank'],
                team['teamNumber'],
                team['qualAverage'],
                team['autoPoints'],
                team['containerPoints'],
                team['coopertitionPoints'],
                team['litterPoints'],
                team['totePoints'],
                team['matchesPlayed']])

        return rankings if len(rankings) > 1 else None

    def parse2016(self, response):
        rankings = [['Rank', 'Team', 'Ranking Score', 'Auto', 'Scale/Challenge', 'Goals', 'Defense', 'Record (W-L-T)', 'Played']]

        for team in response['Rankings']:
            rankings.append([
                team['rank'],
                team['teamNumber'],
                team['sortOrder1'],
                team['sortOrder2'],
                team['sortOrder3'],
                team['sortOrder4'],
                team['sortOrder5'],
                '{}-{}-{}'.format(team['wins'], team['losses'], team['ties']),
                team['matchesPlayed']])

        return rankings if len(rankings) > 1 else None
