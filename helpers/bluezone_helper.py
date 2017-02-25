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
    def get_upcoming_match_predictions(cls, live_events, n=5):
        predictions = {}
        for event in live_events:
            if event.details and event.details.predictions:
                predictions.update(event.details.predictions['match_predictions'])
        return predictions

    @classmethod
    def should_add_match(cls, matches, candidate_match, predictions):
        # Can we put this match in the beginning of the list?
        if matches and candidate_match.predicted_time <= matches[0].predicted_time - cls.BUFFER_AFTER:
            return 0

        for i in range(1, len(matches)):
            # Can we insert this match in between these two
            last_match = matches[i - 1]
            next_match = matches[i]
            if candidate_match.predicted_time >= last_match.predicted_time + cls.BUFFER_AFTER:
                if candidate_match.predicted_time + cls.BUFFER_AFTER <= next_match.predicted_time:
                    if candidate_match.key_name in predictions:
                        return i

        return None

    @classmethod
    def calculate_match_hotness(cls, matches, predictions):
        max_hotness = 0
        min_hotness = float('inf')
        for match in matches:
            if not match.has_been_played and match.key.id() in predictions:
                prediction = predictions[match.key.id()]
                red_score = prediction['red']['score']
                blue_score = prediction['blue']['score']
                if red_score > blue_score:
                    winner_score = red_score
                    loser_score = blue_score
                else:
                    winner_score = blue_score
                    loser_score = red_score

                hotness = winner_score + 2.0*loser_score  # Favor close high scoring matches

                max_hotness = max(max_hotness, hotness)
                min_hotness = min(min_hotness, hotness)
                match.hotness = hotness

        for match in matches:
            match.hotness = 100 * (match.hotness - min_hotness) / (max_hotness - min_hotness)

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
        upcoming_predictions = cls.get_upcoming_match_predictions(live_events)

        cls.calculate_match_hotness(upcoming_matches, upcoming_predictions)
        upcoming_matches.sort(lambda x: -match.hotness)

        bluezone_matches = []
        while len(bluezone_matches) < 5:
            match = upcoming_matches.pop(0)
            now = datetime.datetime.now()
            if match.predicted_time < now:
                # No use switching to this match
                continue

            possible_index = cls.should_add_match(bluezone_matches, match, upcoming_predictions)
            if possible_index is not None:
                bluezone_matches.insert(possible_index, match)
