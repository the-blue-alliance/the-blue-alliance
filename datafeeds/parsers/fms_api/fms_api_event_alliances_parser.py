class FMSAPIEventAlliancesParser(object):
    def parse(self, response):
        alliances = []

        all_null = True
        alliance_num = 0
        for alliance in response['Alliances']:
            alliance_num += 1
            picks = []
            if alliance['captain'] is not None:
                picks.append('frc{}'.format(alliance['captain']))
            if alliance['round1'] is not None:
                picks.append('frc{}'.format(alliance['round1']))
            if alliance['round2'] is not None:
                picks.append('frc{}'.format(alliance['round2']))
            if alliance['round3'] is not None:
                picks.append('frc{}'.format(alliance['round3']))

            # If there are no picks for a given alliance, ignore this alliance
            if len(picks) == 0:
                continue

            # If no name is specified (like in 2015), generate one
            name = alliance['name'] if alliance.get('name', None) else 'Alliance {}'.format(alliance_num)

            backup = 'frc{}'.format(alliance['backup']) if alliance.get('backup', None) else None
            backup_replacement = 'frc{}'.format(alliance['backupReplaced']) if alliance.get('backupReplaced', None) else None

            if all_null and picks != []:
                all_null = False

            alliances.append({
                'picks': picks,
                'declines': [],
                'backup': {'in': backup, 'out': backup_replacement} if backup else None,
                'name': name,
            })

        return None if all_null else alliances
