import cloudstorage
import datetime
import json
import logging

from helpers.firebase.firebase_pusher import FirebasePusher
from helpers.match_helper import MatchHelper
from helpers.outgoing_notification_helper import OutgoingNotificationHelper
from models.event import Event
from models.match import Match
from models.sitevar import Sitevar


class BlueZoneHelper(object):

    TIME_PATTERN = "%Y-%m-%dT%H:%M:%S"
    MAX_TIME_PER_MATCH = datetime.timedelta(minutes=5)
    # BUFFER_AFTER = datetime.timedelta(minutes=4)
    TIME_BUCKET = datetime.timedelta(minutes=5)

    @classmethod
    def get_upcoming_matches(cls, live_events, n=1):
        matches = []
        for event in live_events:
            upcoming_matches = MatchHelper.upcomingMatches(event.matches, n)
            matches.extend(upcoming_matches)
        return matches

    @classmethod
    def get_upcoming_match_predictions(cls, live_events):
        predictions = {}
        for event in live_events:
            if event.details and event.details.predictions:
                try:
                    predictions.update(event.details.predictions.get('match_predictions', {}))
                except Exception, e:
                    logging.info("get_upcoming_match_predictions failed!")
                    logging.info(e)
        return predictions

    # @classmethod
    # def should_add_match(cls, matches, candidate_match, current_match, predictions, current_timeout):
    #     now = datetime.datetime.now()
    #     if current_match and candidate_match.key_name == current_match.key_name and current_timeout is not None and now > current_timeout:
    #         # We've been on this match for too long, try something else
    #         return None

    #     if candidate_match.predicted_time > now + cls.MAX_TIME_PER_MATCH:
    #         # If this match starts too far in the future, don't include it
    #         return None

    #     # If this match conflicts with the current match, don't bother trying
    #     if current_match and candidate_match.predicted_time <= current_match.predicted_time + cls.BUFFER_AFTER:
    #         return None

    #     # Can we put this match in the beginning of the list?
    #     if not matches or candidate_match.predicted_time + cls.BUFFER_AFTER <= matches[0].predicted_time:
    #         return 0

    #     for i in range(1, len(matches)):
    #         # Can we insert this match in between these two
    #         last_match = matches[i - 1]
    #         next_match = matches[i]
    #         if candidate_match.predicted_time >= last_match.predicted_time + cls.BUFFER_AFTER:
    #             if candidate_match.predicted_time + cls.BUFFER_AFTER <= next_match.predicted_time:
    #                 if candidate_match.key_name in predictions:
    #                     return i

    #     # Can we put this match at the end of the list?
    #     if matches and candidate_match.predicted_time >= matches[-1].predicted_time + cls.BUFFER_AFTER:
    #         return len(matches)

    #     return None

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
            else:
                match.hotness = 0

        for match in matches:
            match.hotness = 100 * (match.hotness - min_hotness) / (max_hotness - min_hotness)

    @classmethod
    def build_fake_event(cls):
        return Event(id='bluezone',
                     name='TBA BlueZone (BETA)',
                     event_short='bluezone',
                     year=datetime.datetime.now().year,
                     webcast_json=json.dumps([{'type': 'twitch', 'channel': 'firstinspires'}]))  # Default to this webcast

    @classmethod
    def update_bluezone(cls, live_events):
        """
        Find the current best match to watch
        Currently favors showing something over nothing, is okay with switching
        TO a feed in the middle of a match, but avoids switching FROM a feed
        in the middle of a match.
        1. Get the earliest predicted unplayed match across all live events
        2. Get all matches that start within TIME_BUCKET of that match
        3. Switch to hottest match in that bucket unless MAX_TIME_PER_MATCH is
        hit (in which case blacklist for the future)
        4. Repeat
        """
        now = datetime.datetime.now()
        logging.info("[BLUEZONE] Current time: {}".format(now))
        to_log = '--------------------------------------------------\n'
        to_log += "[BLUEZONE] Current time: {}\n".format(now)

        slack_sitevar = Sitevar.get_or_insert('slack.hookurls')
        slack_url = None
        if slack_sitevar:
            slack_url = slack_sitevar.contents.get('bluezone', '')

        bluezone_config = Sitevar.get_or_insert('bluezone')
        logging.info("[BLUEZONE] Config (updated {}): {}".format(bluezone_config.updated, bluezone_config.contents))
        to_log += "[BLUEZONE] Config (updated {}): {}\n".format(bluezone_config.updated, bluezone_config.contents)
        current_match_key = bluezone_config.contents.get('current_match')
        last_match_key = bluezone_config.contents.get('last_match')
        current_match_predicted_time = bluezone_config.contents.get('current_match_predicted')
        if current_match_predicted_time:
            current_match_predicted_time = datetime.datetime.strptime(current_match_predicted_time, cls.TIME_PATTERN)
        current_match_switch_time = bluezone_config.contents.get('current_match_switch_time')
        if current_match_switch_time:
            current_match_switch_time = datetime.datetime.strptime(current_match_switch_time, cls.TIME_PATTERN)
        else:
            current_match_switch_time = now
        blacklisted_match_keys = bluezone_config.contents.get('blacklisted_matches', set())
        if blacklisted_match_keys:
            blacklisted_match_keys = set(blacklisted_match_keys)
        blacklisted_event_keys = bluezone_config.contents.get('blacklisted_events', set())
        if blacklisted_event_keys:
            blacklisted_event_keys = set(blacklisted_event_keys)

        current_match = Match.get_by_id(current_match_key) if current_match_key else None
        last_match = Match.get_by_id(last_match_key) if last_match_key else None

        logging.info("[BLUEZONE] live_events: {}".format([le.key.id() for le in live_events]))
        to_log += "[BLUEZONE] live_events: {}\n".format([le.key.id() for le in live_events])
        live_events = filter(lambda e: e.webcast_status != 'offline', live_events)
        for event in live_events:  # Fetch all matches and details asynchronously
            event.prep_matches()
            event.prep_details()
        logging.info("[BLUEZONE] Online live_events: {}".format([le.key.id() for le in live_events]))
        to_log += "[BLUEZONE] Online live_events: {}\n".format([le.key.id() for le in live_events])
        upcoming_matches = cls.get_upcoming_matches(live_events)
        upcoming_matches = filter(lambda m: m.predicted_time is not None, upcoming_matches)
        upcoming_predictions = cls.get_upcoming_match_predictions(live_events)

        # (1, 2) Find earliest predicted unplayed match and all other matches
        # that start within TIME_BUCKET of that match
        upcoming_matches.sort(key=lambda match: match.predicted_time)
        potential_matches = []
        time_cutoff = None
        logging.info("[BLUEZONE] all upcoming matches sorted by predicted time: {}".format([um.key.id() for um in upcoming_matches]))
        to_log += "[BLUEZONE] all upcoming sorted by predicted time: {}\n".format([um.key.id() for um in upcoming_matches])
        for match in upcoming_matches:
            if match.predicted_time:
                if time_cutoff is None:
                    time_cutoff = match.predicted_time + cls.TIME_BUCKET
                    potential_matches.append(match)
                elif match.predicted_time < time_cutoff:
                    potential_matches.append(match)
                else:
                    break  # Matches are sorted by predicted_time
        logging.info("[BLUEZONE] potential_matches sorted by predicted time: {}".format([pm.key.id() for pm in potential_matches]))
        to_log += "[BLUEZONE] potential_matches sorted by predicted time: {}\n".format([pm.key.id() for pm in potential_matches])

        # (3) Choose hottest match that's not blacklisted
        cls.calculate_match_hotness(potential_matches, upcoming_predictions)
        potential_matches.sort(key=lambda match: -match.hotness)
        logging.info("[BLUEZONE] potential_matches sorted by hotness: {}".format([pm.key.id() for pm in potential_matches]))
        to_log += "[BLUEZONE] potential_matches sorted by hotness: {}\n".format([pm.key.id() for pm in potential_matches])

        bluezone_matches = []
        new_blacklisted_match_keys = set()

        # If the current match hasn't finished yet, don't even bother
        cutoff_time = current_match_switch_time + cls.MAX_TIME_PER_MATCH
        logging.info("[BLUEZONE] Current match played? {}, now = {}, cutoff = {}".format(current_match.has_been_played if current_match else None, now, cutoff_time))
        to_log += "[BLUEZONE] Current match played? {}, now = {}, cutoff = {}\n".format(current_match.has_been_played if current_match else None, now, cutoff_time)
        if current_match and not current_match.has_been_played and now < cutoff_time \
                and current_match_key not in blacklisted_match_keys \
                and current_match.event_key_name not in blacklisted_event_keys:
            logging.info("[BLUEZONE] Keeping current match {}".format(current_match.key.id()))
            to_log += "[BLUEZONE] Keeping current match {}\n".format(current_match.key.id())
            bluezone_matches.append(current_match)

        for match in potential_matches:
            if len(bluezone_matches) >= 2:  # one current, one future
                break
            logging.info("[BLUEZONE] Trying potential match: {}".format(match.key.id()))
            to_log += "[BLUEZONE] Trying potential match: {}\n".format(match.key.id())
            if filter(lambda m: m.key.id() == match.key.id(), bluezone_matches):
                logging.info("[BLUEZONE] Match {} already chosen".format(match.key.id()))
                to_log += "[BLUEZONE] Match {} already chosen\n".format(match.key.id())
                continue
            if match.event_key_name in blacklisted_event_keys:
                logging.info("[BLUEZONE] Event {} is blacklisted, skipping...".format(match.event_key_name))
                to_log += "[BLUEZONE] Event {} is blacklisted, skipping...\n".format(match.event_key_name)
                continue
            if match.key.id() not in blacklisted_match_keys:
                if match.key.id() == current_match_key:
                    if current_match_predicted_time and cutoff_time < now and len(potential_matches) > 1:
                        # We've been on this match too long
                        new_blacklisted_match_keys.add(match.key.id())
                        logging.info("[BLUEZONE] Adding match to blacklist: {}".format(match.key.id()))
                        to_log += "[BLUEZONE] Adding match to blacklist: {}\n".format(match.key.id())
                        logging.info("[BLUEZONE] scheduled time: {}, now: {}".format(current_match_predicted_time, now))
                        to_log += "[BLUEZONE] scheduled time: {}, now: {}\n".format(current_match_predicted_time, now)
                        OutgoingNotificationHelper.send_slack_alert(slack_url, "Blacklisting match {}. Predicted time: {}, now: {}".format(match.key.id(), current_match_predicted_time, now))
                    else:
                        # We can continue to use this match
                        bluezone_matches.append(match)
                        logging.info("[BLUEZONE] Continuing to use match: {}".format(match.key.id()))
                        to_log += "[BLUEZONE] Continuing to use match: {}\n".format(match.key.id())
                else:
                    # Found a new good match
                    bluezone_matches.append(match)
                    logging.info("[BLUEZONE] Found a good new match: {}".format(match.key.id()))
                    to_log += "[BLUEZONE] Found a good new match: {}\n".format(match.key.id())
            else:
                logging.info("[BLUEZONE] Match already blacklisted: {}".format(match.key.id()))
                to_log += "[BLUEZONE] Match already blacklisted: {}\n".format(match.key.id())
                new_blacklisted_match_keys.add(match.key.id())

        if not bluezone_matches:
            logging.info("[BLUEZONE] No match selected")
            to_log += "[BLUEZONE] No match selected\n"

        logging.info("[BLUEZONE] All selected matches: {}".format([m.key.id() for m in bluezone_matches]))
        to_log += "[BLUEZONE] All selected matches: {}\n".format([m.key.id() for m in bluezone_matches])

        # (3) Switch to hottest match
        fake_event = cls.build_fake_event()
        if bluezone_matches:
            bluezone_match = bluezone_matches[0]
            real_event = filter(lambda x: x.key_name == bluezone_match.event_key_name, live_events)[0]

            # Create Fake event for return
            fake_event.webcast_json = json.dumps([real_event.current_webcasts[0]])

            if bluezone_match.key_name != current_match_key:
                current_match_switch_time = now
                logging.info("[BLUEZONE] Switching to: {}".format(bluezone_match.key.id()))
                to_log += "[BLUEZONE] Switching to: {}\n".format(bluezone_match.key.id())
                OutgoingNotificationHelper.send_slack_alert(slack_url, "It is now {}. Switching BlueZone to {}, scheduled for {} and predicted to be at {}.".format(now, bluezone_match.key.id(), bluezone_match.time, bluezone_match.predicted_time))
                if not current_match or current_match.has_been_played:
                    last_match = current_match

            # Only need to update if things changed
            if bluezone_match.key_name != current_match_key or new_blacklisted_match_keys != blacklisted_match_keys:
                FirebasePusher.update_event(fake_event)
                bluezone_config.contents = {
                    'current_match': bluezone_match.key.id(),
                    'last_match': last_match.key.id() if last_match else '',
                    'current_match_predicted': bluezone_match.predicted_time.strftime(cls.TIME_PATTERN),
                    'blacklisted_matches': list(new_blacklisted_match_keys),
                    'blacklisted_events': list(blacklisted_event_keys),
                    'current_match_switch_time': current_match_switch_time.strftime(cls.TIME_PATTERN),
                }
                bluezone_config.put()

                # Log to cloudstorage
                log_dir = '/tbatv-prod-hrd.appspot.com/tba-logging/bluezone/'
                log_file = 'bluezone_{}.txt'.format(now.date())
                full_path = log_dir + log_file

                existing_contents = ''
                if full_path in set([f.filename for f in cloudstorage.listbucket(log_dir)]):
                    with cloudstorage.open(full_path, 'r') as existing_file:
                        existing_contents = existing_file.read()

                with cloudstorage.open(full_path, 'w') as new_file:
                    new_file.write(existing_contents + to_log)

            bluezone_matches.insert(0, last_match)
            bluezone_matches = filter(lambda m: m is not None, bluezone_matches)
            FirebasePusher.replace_event_matches('bluezone', bluezone_matches)

        return fake_event
