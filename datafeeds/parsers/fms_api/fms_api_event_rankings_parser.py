class FMSAPIEventRankingsParser(object):
    def parse(self, response):
        """
        This currently only works for the 2015 game.
        """
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

        return rankings
