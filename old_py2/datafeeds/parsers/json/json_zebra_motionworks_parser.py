import json
import re
from datafeeds.parser_base import ParserInputException, ParserBase


class JSONZebraMotionWorksParser(ParserBase):
    @classmethod
    def parse(cls, zebra_motion_json):
        """
        Parse JSON that contains Zebra MotionWorks data
        Format is as follows:
        [{
            key: '2020casj_qm1',
            times: [<elapsed time (float seconds)>, 0.0, 0.5, 1.0, 1.5, ...],
            alliances: {
                red: [
                    {
                        team_key: "frc254",
                        xs: [<float feet or null>, null, 1.2, 1.3, 1.4, ...],
                        ys: [<float feet or null>, null, 0.1, 0.1, 0.1, ...],
                    },
                    {
                        team_key: "frc971",
                        xs: [1.1, 1.2, 1.3, 1.4, ...],
                        ys: [0.1, 0.1, 0.1, 0.1, ...],
                    },
                    ...
                ],
                blue: [...],
            }
        }]
        """
        try:
            data = json.loads(zebra_motion_json)
        except Exception:
            raise ParserInputException("Invalid JSON. Please check input.")

        parsed_data = []
        for zebra_data in data:
            # Check 'times' is an array of floats
            times = zebra_data.get('times', [])
            if not isinstance(times, list):
                raise ParserInputException("Zebra MotionWorks data must have a array of 'times'.")
            data_length = len(times)
            if data_length == 0:
                raise ParserInputException("Length of 'times' must be non-zero.")
            for time in times:
                if not isinstance(time, float):
                    raise ParserInputException("'times' must be an array of floats.")

            # Check 'alliances'
            alliances = zebra_data.get('alliances')
            if not isinstance(alliances, dict):
                raise ParserInputException("Zebra MotionWorks data must have a dictionary of 'alliances'.")

            red = cls._parse_alliance(alliances.get('red', []), data_length)
            blue = cls._parse_alliance(alliances.get('blue', []), data_length)

            parsed_data.append({
                'key': zebra_data.get('key'),
                'times': times,
                'alliances': {
                    'red': red,
                    'blue': blue,
                },
            })
        return parsed_data

    @classmethod
    def _parse_alliance(cls, alliance, data_length):
        if len(alliance) != 3:
            # Not necessarily true in the future, but encofing this for now
            raise ParserInputException("Must have 3 teams per alliance.")

        parsed_alliance = []
        for team in alliance:
            parsed_alliance.append(cls._parse_team(team, data_length))
        return parsed_alliance

    @classmethod
    def _parse_team(cls, team, data_length):
        # Check team_key format
        team_key = team.get('team_key')
        if not re.match(r'frc\d+', str(team_key)):
            raise ParserInputException("Bad 'team_key': '{}'. Must follow format 'frcXXX'.".format(team_key))

        # Check xs, ys format
        xs = cls._parse_coord(team.get('xs', []), data_length)
        ys = cls._parse_coord(team.get('ys', []), data_length)
        for x, y in zip(xs, ys):
            if (x is None and y is not None) or (x is not None and y is None):
                raise ParserInputException("Coordinate data at a given time index for a given team may not have a mix of null and non-null values.")

        parsed_team = {
            'team_key': team_key,
            'xs': xs,
            'ys': ys,
        }
        return parsed_team

    @classmethod
    def _parse_coord(cls, coords, data_length):
        if len(coords) != data_length:
            raise ParserInputException("Length of coordinate data must be consistent.")
        for coord in coords:
            if not (isinstance(coord, float) or coord is None):
                raise ParserInputException("Coordinate data must be an array of floats or nulls.")
        return coords
