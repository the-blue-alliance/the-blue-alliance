class RankingIndexes(object):

	TEAM_NUMBER = 1

	MATCHES_PLAYED = {
		2016: -1,
		2015: -1,
		2014: -1,
		2013: -1,
		2012: -1,
		2011: 5,
		2010: 2,
		2009: 5,
		2008: 5,
		2007: 5
	}

	CUMULATIVE_RANKING_SCORE = {
		2016: 2,
		# 2015 is excluded because teams are already ranked by an average
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