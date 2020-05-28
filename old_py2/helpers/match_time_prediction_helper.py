import cloudstorage
import datetime
import time

from google.appengine.api import memcache
from helpers.match_manipulator import MatchManipulator
from models.match import Match


class MatchTimePredictionHelper(object):

    EPOCH = datetime.datetime.fromtimestamp(0)
    MAX_IN_PAST = datetime.timedelta(minutes=-4)  # One match length, ish
    MAX_SCHEDULE_OFFSET = datetime.timedelta(minutes=-15)  # Never predict more than this much ahead of schedule

    @classmethod
    def as_local(cls, time, timezone):
        import pytz
        if not time:
            return None
        return pytz.utc.localize(time).astimezone(timezone)

    @classmethod
    def as_utc(cls, time):
        if time.utcoffset():
            return (time - time.utcoffset()).replace(tzinfo=None)
        return time

    @classmethod
    def timestamp(cls, d):
        return time.mktime(d.timetuple())

    @classmethod
    def compute_average_cycle_time(cls, played_matches, next_unplayed, timezone):
        """
        Compute the average cycle time of the given matches, but only for the current day
        :param played_matches: The matches for this event that have been played
        :param next_unplayed: The next match to be played
        :param timezone: The timezone object, for computing local times
        :return: The average cycle time, in seconds, or None if not enough info
        """
        import numpy as np

        cycles = []

        # Sort matches by when they were actually played
        # This should account for out of order replays messing with the computations
        played_matches.sort(key=lambda x: x.actual_time)

        # Next match start time (in local time)
        next_match_start = cls.as_local(next_unplayed.time, timezone)

        # Find the first played match of the same day as the next match to be played
        start_of_day = None
        for i in range(0, len(played_matches)):
            scheduled_time = cls.as_local(played_matches[i].time, timezone)
            if scheduled_time.day == next_match_start.day:
                start_of_day = i
                break

        if start_of_day is None:
            return None

        # Compute cycle times for matches on this day
        for i in range(start_of_day + 1, len(played_matches)):
            cycle = cls.timestamp(played_matches[i].actual_time) - cls.timestamp(played_matches[i - 1].actual_time)

            # Discard (with 0 weight) outlier cycles that take too long (>150% of the schedule)
            # We want to bias our average to be low, so we don't "overshoot" our predictions
            # So we simply discard outliers instead of letting them skew the average
            # Additionally, discard matches with breaks (like lunch) in between. We find those
            # when we see a scheduled time between matches larger than 15 minutes
            scheduled_cycle = cls.timestamp(played_matches[i].time) - cls.timestamp(played_matches[i - 1].time)
            if scheduled_cycle < 15 * 60 and cycle <= scheduled_cycle * 1.5:
                # Bias the times towards the schedule
                cycle = (0.7 * cycle) + (0.3 * scheduled_cycle)
                cycles.append(cycle)

        return np.percentile(cycles, 35) if cycles else None

    @classmethod
    def predict_future_matches(cls, event_key, played_matches, unplayed_matches, timezone, is_live):
        """
        Add match time predictions for future matches
        """
        to_log = '--------------------------------------------------\n'
        to_log += "[TIME PREDICTIONS] Current time: {}\n".format(datetime.datetime.now())
        to_log += "[TIME PREDICTIONS] Current event: {}\n".format(event_key)

        last_match = played_matches[-1] if played_matches else None
        next_match = unplayed_matches[0] if unplayed_matches else None

        if last_match:
            to_log += "[TIME PREDICTIONS] Last Match: {}, Actual Time: {}, Schedule: {} - {}, Predicted: {} - {}\n"\
                .format(last_match.key_name, cls.as_local(last_match.actual_time, timezone),
                        cls.as_local(last_match.time, timezone), last_match.schedule_error_str,
                        cls.as_local(last_match.predicted_time, timezone), last_match.prediction_error_str)

        if next_match:
            to_log += "[TIME PREDICTIONS] Next Match: {}, Schedule: {}, Last Predicted: {}\n"\
                .format(next_match.key_name, cls.as_local(next_match.time, timezone), cls.as_local(next_match.predicted_time, timezone))

        if len(played_matches) >= 2:
            # Just for some logging
            two_ago = played_matches[-2]
            if last_match.actual_time and two_ago.actual_time:
                cycle = last_match.actual_time - two_ago.actual_time
                s = int(cycle.total_seconds())
                to_log += '[TIME PREDICTIONS] Last Cycle: {:02}:{:02}:{:02}\n'.format(s // 3600, s % 3600 // 60, s % 60)

        if not next_match or (last_match and not last_match.time) or (last_match and not last_match.actual_time):
            # Nothing to predict
            return

        last_match_day = cls.as_local(last_match.time, timezone).day if last_match else None
        average_cycle_time = cls.compute_average_cycle_time(played_matches, next_match, timezone)
        last = last_match

        # Only write logs if this is the first time after a new match is played
        memcache_key = "time_prediction:last_match:{}".format(event_key)
        last_played = memcache.get(memcache_key)
        write_logs = False
        if last_match and last_match.key_name != last_played:
            write_logs = True
            memcache.set(memcache_key, last_match.key_name, 60*60*24)

        if average_cycle_time:
            average_cycle_time = int(average_cycle_time)
            to_log += "[TIME PREDICTIONS] Average Cycle Time: {:02}:{:02}:{:02}\n".format(average_cycle_time // 3600, average_cycle_time % 3600 // 60, average_cycle_time % 60)

        # Run predictions for all unplayed matches on this day and comp level
        last_comp_level = next_match.comp_level if next_match else None
        now = datetime.datetime.now(timezone) + cls.MAX_IN_PAST if is_live else cls.as_local(cls.EPOCH, timezone)
        first_unplayed_timedelta = None
        for i in range(0, len(unplayed_matches)):
            match = unplayed_matches[i]
            if not match.time:
                continue

            if first_unplayed_timedelta is None:
                first_unplayed_timedelta = now - cls.as_local(match.time, timezone)
            if first_unplayed_timedelta < datetime.timedelta(seconds = 0):
                first_unplayed_timedelta = datetime.timedelta(seconds = 0)

            scheduled_time = cls.as_local(match.time, timezone)
            if (scheduled_time.day != last_match_day and last_match_day is not None) \
                    or last_comp_level != match.comp_level:
                if i == 0:
                    write_logs = False
                # Use predicted = scheduled once we exhaust all unplayed matches on this day or move to a new comp level
                match.predicted_time = cls.as_utc(cls.as_local(match.time, timezone) + first_unplayed_timedelta)
                continue

            # For the first iteration, base the predictions off the newest known actual start time
            # Otherwise, use the predicted start time of the previously processed match
            last_predicted = None
            if last_match:
                cycle_time = average_cycle_time if average_cycle_time else 60 * 7  # Default to 7 min
                base_time = max(
                    cls.as_local(last_match.actual_time, timezone),
                    now - datetime.timedelta(seconds=cycle_time)
                )
                last_predicted = base_time if i == 0 else cls.as_local(last.predicted_time, timezone)
            if last_predicted and average_cycle_time:
                predicted = last_predicted + datetime.timedelta(seconds=average_cycle_time)
            else:
                # Shift predicted time by the amouont the first match is behind
                predicted = cls.as_local(match.time, timezone) + first_unplayed_timedelta

            # Never predict a match to happen more than 15 minutes ahead of schedule or in the past
            # Except for playoff matches, which we allow to be any amount early (since all schedule
            # bets are off due to canceled tiebreaker matches).
            # However, if the event is not live (we're running the job manually for a single event),
            # then allow predicted times to be in the past.
            earliest_possible = cls.as_local(match.time + cls.MAX_SCHEDULE_OFFSET, timezone) \
                if match.comp_level not in Match.ELIM_LEVELS else cls.as_local(cls.EPOCH, timezone)
            match.predicted_time = max(cls.as_utc(predicted), cls.as_utc(earliest_possible))
            last = match
            last_comp_level = match.comp_level

        MatchManipulator.createOrUpdate(unplayed_matches)

        # Log to cloudstorage, but only if we have something new
        if not write_logs:
            return
        log_dir = '/tbatv-prod-hrd.appspot.com/tba-logging/match-time-predictions/'
        log_file = '{}.txt'.format(event_key)
        full_path = log_dir + log_file

        existing_contents = ''
        if full_path in set([f.filename for f in cloudstorage.listbucket(log_dir)]):
            with cloudstorage.open(full_path, 'r') as existing_file:
                existing_contents = existing_file.read()

        with cloudstorage.open(full_path, 'w') as new_file:
            new_file.write(existing_contents + to_log)
