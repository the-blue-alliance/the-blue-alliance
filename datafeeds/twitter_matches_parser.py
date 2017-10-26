import logging

from datafeeds.parser_base import ParserBase

ELIM_MAPPING = {
    '1': 'qf1m1',
    '2': 'qf2m1',
    '3': 'qf3m1',
    '4': 'qf4m1',
    '5': 'qf1m2',
    '6': 'qf2m2',
    '7': 'qf3m2',
    '8': 'qf4m2',
    '9': 'qf1m3',
    '10': 'qf2m3',
    '11': 'qf3m3',
    '12': 'qf4m3',
    '13': 'sf1m1',
    '14': 'sf2m1',
    '15': 'sf1m2',
    '16': 'sf2m2',
    '17': 'sf1m3',
    '18': 'sf2m3',
    '19': 'f1m1',
    '20': 'f1m2',
    '21': 'f1m3',
}


class TwitterMatchesParser(ParserBase):
    @classmethod
    def parse(self, tweet):
        """
        Parse a tweet from FRCFMS.
        Returns a tuple in the following form:
        event_short, match result in CSV format

        Match CSV format is as follows:
        match_id, red1, red2, red3, blue1, blue2, blue3, red score, blue score

        Example formats of match_id:
        qm1, sf2m1, f1m1
        """
        i = tweet.split()
        try:
            event_short = str(i[0][4:].lower())
            kind = str(i[2])
            number = str(i[4])
            red_final = str(i[6])
            blue_final = str(i[8])
            red_teams = str(i[10]) + ',' + str(i[11]) + ',' + str(i[12])
            blue_teams = str(i[14]) + ',' + str(i[15]) + ',' + str(i[16])
        except IndexError:
            logging.warning("Failed to parse tweet: {}".format(tweet))
            return None, tweet

        if kind == 'E':
            match_id = ELIM_MAPPING[number]
        elif kind == 'Q':
            match_id = 'qm' + number
        else:
            match_id = '???' + number

        match_csv_row = match_id + ',' + red_teams + ',' + blue_teams + ',' + red_final + ',' + blue_final

        return event_short, match_csv_row
