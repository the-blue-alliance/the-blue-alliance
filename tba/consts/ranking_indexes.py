class RankingIndexes(object):
    TEAM_NUMBER = 1

    MATCHES_PLAYED = {
        2019: 9,
        2018: 9,
        2017: 10,
        2016: 8,
        2015: 8,
        2014: 9,
        2013: 8,
        2012: 9,
        2011: 5,
        2010: 2,
        2009: 5,
        2008: 5,
        2007: 5
    }

    CUMULATIVE_RANKING_SCORE = {
        2019: 2,
        2018: 2,
        2017: 2,  # In 2017, this is RP/Match
        2016: 2,
        2015: 2,  # In 2015, this is average qual score
        2014: 2,
        2013: 2,
        2012: 2,
        2011: 6,
        2010: 3,
        2009: 6,
        2008: 6,
        2007: 6
    }

    CUMULATIVE_RANKING_YEARS = CUMULATIVE_RANKING_SCORE.keys()

    # Get the record out of the rankings arrays
    # If the value is a tuple, it represents the index of (wins, losses, ties)
    # If the value is a single int, that index contains the formatted record
    # The value is None if we can't get record from rankings in the given year
    RECORD_INDEXES = {
        2007: (2, 3, 4),
        2008: (2, 3, 4),
        2009: (2, 3, 4),
        2010: None,  # The 2010 ranking system gets the last laugh here...
        2011: (2, 3, 4),
        2012: 7,
        2013: 6,
        2014: 7,
        2015: None,
        2016: 7,
        2017: 8,
        2018: 7,
        2019: 7,
    }
