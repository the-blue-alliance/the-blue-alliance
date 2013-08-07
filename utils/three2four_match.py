# three2four_match.py
#
# Converts a CSV export of TBAv3 SQL Matches into the read CSV format for
# TBAv4 on Google App Engine. Sets no_auto_update to true.
#
# Incoming CSV format:
# event.year, event.eventshort, complevel, matchnumber, red1, red2, red3, blue1, blue2, blue3, redscore, bluescore
#
# python three2four_match.py -i old_matches.csv -o new_matches.csv
#
# -gregmarra 6 Sept 2010

import csv
import logging
import math
from optparse import OptionParser

COMPLEVELS = {
    10: "qm",
    20: "ef",
    30: "qf",
    40: "sf",
    50: "f"
}

FRC_GAMES_BY_YEAR = {
    2010: "frc_2010_bkwy",
    2009: "frc_2009_lncy",
    2008: "frc_2008_ovdr",
    2007: "frc_2007_rkrl",
    2006: "frc_2006_amhi",
    2005: "frc_2005_trpl",
    2004: "frc_2004_frnz",
    2003: "frc_2003_stck",
    2002: "frc_2002_znzl",
    2001: "frc_2001_dbdy",
    2000: "frc_2000_coop",
    1999: "frc_1999_trbl",
    1998: "frc_1998_lddr",
    1997: "frc_1997_trdt",
    1996: "frc_1996_hxgn",
    1995: "frc_1995_rmpr",
    1994: "frc_1994_tpwr",
    1993: "frc_1993_rgrg",
    1992: "frc_1992_maiz"
}


def parse_row(row):
    """Parse a row into a nice dictionary."""
    old_match = dict()
    old_match["year"] = row[0]
    old_match["eventshort"] = row[1]
    old_match["complevel"] = row[2]
    old_match["matchnumber"] = row[3]
    old_match["red1"] = row[4]
    old_match["red2"] = row[5]
    old_match["red3"] = row[6]
    old_match["blue1"] = row[7]
    old_match["blue2"] = row[8]
    old_match["blue3"] = row[9]
    old_match["redscore"] = row[10]
    old_match["bluescore"] = row[11]
    return old_match


def legal_teams(teams):
    """Return a list of teams that are possible."""
    good_teams = list()
    for team in teams:
        try:
            team_number = int(team)
            if team_number > 0:
                good_teams.append(team_number)
        except ValueError:
            logging.warning(str(team) + " is not a valid team number.")

    good_teams = ["frc" + str(team) for team in good_teams]
    return good_teams


def build_new_match(old_match):
    """Build a new match."""
    match = dict()
    match["event"] = old_match["year"] + old_match["eventshort"]
    try:
        match["comp_level"] = COMPLEVELS[int(old_match["complevel"])]
    except Exception as e:
        logging.error("Bad comp_level: " + str(old_match["complevel"]))
        return None
    match["game"] = FRC_GAMES_BY_YEAR[int(old_match["year"])]

    red_teams = legal_teams([old_match["red1"], old_match["red2"], old_match["red3"]])
    blue_teams = legal_teams([old_match["blue1"], old_match["blue2"], old_match["blue3"]])

    match["alliances_json"] = {
        "red": {
            "teams": red_teams,
            "score": old_match["redscore"]
        },
        "blue": {
            "teams": blue_teams,
            "score": old_match["bluescore"]
        }
    }
    match["team_key_names"] = red_teams + blue_teams

    if match["comp_level"] == "qm":
        match["match_number"] = old_match["matchnumber"]
        match["set_number"] = 1
        match["key"] = match["event"] + "_qm" + match["match_number"]
    else:
        match["match_number"] = str(int(old_match["matchnumber"]) % 10)
        match["set_number"] = str(int(math.floor(int(old_match["matchnumber"]) / 10.0)))
        match["key"] = match["event"] + "_" + match["comp_level"] + match["set_number"] + "m" + match["match_number"]

    match["no_auto_update"] = "TRUE"

    return match


def main():
    parser = OptionParser()
    parser.add_option("-i", "--input_file", type="string",
                      help="Input TBA SQL export CSV")
    parser.add_option("-o", "--output_file", type="string",
                      help="Output CSV")
    options, args = parser.parse_args()

    matches = list()

    matchReader = csv.reader(open(options.input_file, 'rb'), delimiter=',')
    for row in matchReader:
        old_match = parse_row(row)
        new_match = build_new_match(old_match)
        if new_match:
            matches.append(new_match)

    matchWriter = csv.writer(open(options.output_file, 'wb'), delimiter=',',
                             quotechar='"', quoting=csv.QUOTE_MINIMAL)
    matchWriter.writerow(["key", "event", "game", "comp_level", "set_number", "match_number", "team_key_names", "alliances_json", "no_auto_update"])
    for match in matches:
        matchWriter.writerow([match["key"], match["event"], match["game"], match["comp_level"], match["set_number"], match["match_number"], match["team_key_names"], match["alliances_json"], match["no_auto_update"]])

if __name__ == "__main__":
    main()
