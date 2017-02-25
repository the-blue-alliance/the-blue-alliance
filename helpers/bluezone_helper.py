import datetime

from helpers.match_helper import MatchHelper


class BlueZoneHelper(object):

    BUFFER_AFTER = 4 * 40  # 4 minutes

    @classmethod
    def get_upcoming_matches(cls, live_events, n=5):
        matches = []
        for event in live_events:
            event_matches = event.matches
            upcoming_matches = MatchHelper.upcomingMatches(event_matches, n)
            matches.extend(upcoming_matches)
        return matches

    @classmethod
    def should_add_match(cls, matches, candidate_match):
        # Can we put this match in the beginning of the list?
        if matches and candidate_match.predicted_time <= matches[0].predicted_time - cls.BUFFER_AFTER:
            return 0

        for i in range(1, len(matches)):
            # Can we insert this match in between these two
            last_match = matches[i - 1]
            next_match = matches[i]
            if candidate_match.predicted_time >= last_match.predicted_time + cls.BUFFER_AFTER and candidate_match.predicted_time + cls.BUFFER_AFTER <= next_match.predicted_time:
                return i

        return None

    @classmethod
    def update_bluezone(cls, live_events):
        """
        Find the current best match to watch
        1. Get the 5 matches to be played for each live event
        2. Calculate "hotness" for each match and normalize among themselves
        3. Sort by hotness
        4.
        """
        upcoming_matches = cls.get_upcoming_matches(live_events)
        # TODO calculate hotness and sort

        bluezone_matches = []
        while len(bluezone_matches)< 5:
            match = upcoming_matches.pop(0)
            now = datetime.datetime.now()
            if match.predicted_time < now:
                # No use switching to this match
                continue

            possible_index = cls.should_add_match(bluezone_matches, match)
            if possible_index:
                bluezone_matches.insert(possible_index, match)
