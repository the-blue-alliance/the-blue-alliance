from helpers.rankings_helper import RankingsHelper


class FMSAPIEventRankingsParser(object):
    def __init__(self, year):
        self.year = year

    def parse(self, response):
        parsers = {
            2015: self.parse2015,
            2016: self.parse2016,
            2017: self.parse2017,
        }
        if self.year not in parsers:
            return None
        else:
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

    def parse2017(self, response):
        rankings = [['Rank', 'Team', 'Ranking Score', 'Match Points', 'Auto', 'Rotor', 'Touchpad', 'Pressure', 'Record (W-L-T)', 'Played']]

        for team in response['Rankings']:
            rankings.append([
                team['rank'],
                team['teamNumber'],
                team['sortOrder1'],
                team['sortOrder2'],
                team['sortOrder3'],
                team['sortOrder4'],
                team['sortOrder5'],
                team['sortOrder6'],
                '{}-{}-{}'.format(team['wins'], team['losses'], team['ties']),
                team['matchesPlayed']])

        return rankings if len(rankings) > 1 else None


class FMSAPIEventRankings2Parser(object):
    def __init__(self, year):
        self.year = year

    def parse(self, response):
        rankings = []
        for team in response['Rankings']:
            count = 1
            order_name = 'sortOrder{}'.format(count)
            sort_orders = []
            while order_name in team:
                sort_orders.append(team[order_name])
                count += 1
                order_name = 'sortOrder{}'.format(count)

            rankings.append(RankingsHelper.build_ranking(
                self.year, team['rank'], 'frc{}'.format(team['teamNumber']),
                team['wins'], team['losses'], team['ties'],
                team['qualAverage'], team['matchesPlayed'], team['dq'], sort_orders))

        return rankings
