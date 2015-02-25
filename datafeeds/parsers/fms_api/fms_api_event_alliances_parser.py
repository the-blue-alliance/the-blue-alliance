class FMSAPIEventAlliancesParser(object):
    def parse(self, response):
        alliances = []

        all_null = True
        for alliance in response['Alliances']:
            picks = []
            if alliance['captain'] is not None:
                picks.append('frc{}'.format(alliance['captain']))
            if alliance['round1'] is not None:
                picks.append('frc{}'.format(alliance['round1']))
            if alliance['round2'] is not None:
                picks.append('frc{}'.format(alliance['round2']))
            if alliance['round3'] is not None:
                picks.append('frc{}'.format(alliance['round3']))

            if all_null and picks != []:
                all_null = False

            alliances.append({
                'picks': picks,
                'declines': []
            })

        return None if all_null else alliances
