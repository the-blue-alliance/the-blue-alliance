import datetime
import json

from helpers.firebase.firebase_pusher import FirebasePusher
from helpers.match_helper import MatchHelper
from models.event import Event
from models.match import Match
from models.sitevar import Sitevar


class BlueZoneHelper(object):

    MAX_TIME_PER_MATCH = datetime.timedelta(minutes=7)
    BUFFER_AFTER = datetime.timedelta(minutes=4)

    @classmethod
    def get_upcoming_matches(cls, live_events, n=1):
        matches = []
        for event in live_events:
            event_matches = event.matches
            upcoming_matches = MatchHelper.upcomingMatches(event_matches, n)
            matches.extend(upcoming_matches)
        return matches

    @classmethod
    def get_upcoming_match_predictions(cls, live_events):
        predictions = {}
        for event in live_events:
            if event.details and event.details.predictions:
                predictions.update(event.details.predictions['match_predictions'])
        return predictions

    @classmethod
    def should_add_match(cls, matches, candidate_match, current_match, predictions):
        # If this match conflicts with the current match, don't bother trying
        if current_match and candidate_match.predicted_time <= current_match.predicted_time + cls.BUFFER_AFTER:
            return None

        # Can we put this match in the beginning of the list?
        if not matches or candidate_match.predicted_time + cls.BUFFER_AFTER <= matches[0].predicted_time:
            return 0

        for i in range(1, len(matches)):
            # Can we insert this match in between these two
            last_match = matches[i - 1]
            next_match = matches[i]
            if candidate_match.predicted_time >= last_match.predicted_time + cls.BUFFER_AFTER:
                if candidate_match.predicted_time + cls.BUFFER_AFTER <= next_match.predicted_time:
                    if candidate_match.key_name in predictions:
                        return i

        # Can we put this match at the end of the list?
        if matches and candidate_match.predicted_time >= matches[-1].predicted_time + cls.BUFFER_AFTER:
            return len(matches)

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
    def build_fake_event(cls):
        return Event(id='bluezone',
                     name='TBA BlueZone',
                     event_short='bluezone',
                     year=datetime.datetime.now().year)

    @classmethod
    def update_bluezone(cls, live_events):
        """
        Find the current best match to watch
        1. Get the next match to be played for each live event
        2. Calculate "hotness" for each match and normalize among themselves
        3. Sort by hotness
        4.
        """
        bluezone_config = Sitevar.get_or_insert('bluezone')
        current_match_key = bluezone_config.contents.get('current_match')
        current_match_added_time = bluezone_config.contents.get('current_match_added')
        current_stream = bluezone_config.contents.get('current_webcast')

        current_match = Match.get_by_id(current_match_key) if current_match_key else None
        upcoming_matches = cls.get_upcoming_matches(live_events)
        upcoming_predictions = cls.get_upcoming_match_predictions(live_events)

        cls.calculate_match_hotness(upcoming_matches, upcoming_predictions)
        upcoming_matches.sort(lambda x: -match.hotness)

        # TODO don't get stuck on a single match if its event gets delayed

        bluezone_matches = []
        now = datetime.datetime.now()
        while len(bluezone_matches) < 1 and upcoming_matches:
            match = upcoming_matches.pop(0)
            if match.predicted_time < now:
                # No use switching to this match
                continue

            possible_index = cls.should_add_match(bluezone_matches, match, current_match,
                                                  upcoming_predictions)
            if possible_index is not None:
                bluezone_matches.insert(possible_index, match)

        if current_match.has_been_played and bluezone_matches:
            next_match = bluezone_matches[0]
            real_event = filter(lambda x: x.key_name == next_match.event_key_name, live_events)[0]
            if real_event.webcast:
                fake_event = cls.build_fake_event()
                # TODO should handle multiple webcasts per event
                fake_event.webcast_json = json.dumps([real_event.webcast[0]])
                FirebasePusher.update_event(fake_event)
                bluezone_config.contents['current_webcast'] = real_event.webcast[0]
                bluezone_config.contents['current_match'] = next_match.event_key_name
                bluezone_config.contents['current_match_added'] = "{}".format(now)
                bluezone_config.put()

                # TODO log this change to Cloud Storage

        if bluezone_matches:
            FirebasePusher.replace_event_matches('bluezone', bluezone_matches)
