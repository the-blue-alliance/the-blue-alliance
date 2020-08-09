from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.match import Match


class MatchManipulator(ManipulatorBase[Match]):
    """
    Handle Match database writes.
    """

    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_match_cache_keys_and_controllers(affected_refs)
    """

    """
    @classmethod
    def postDeleteHook(cls, matches):
        '''
        To run after the match has been deleted.
        '''
        for match in matches:
            try:
                FirebasePusher.delete_match(match)
            except Exception:
                logging.warning("Firebase delete_match failed!")
    """

    """
    @classmethod
    def postUpdateHook(cls, matches, updated_attr_list, is_new_list):
        '''
        To run after the match has been updated.
        Send push notifications to subscribed users
        Only if the match is part of an active event
        '''
        unplayed_match_events = []
        for (match, updated_attrs, is_new) in zip(matches, updated_attr_list, is_new_list):
            event = match.event.get()
            # Only continue if the event is currently happening
            if event.now:
                if match.has_been_played:
                    if is_new or 'alliances_json' in updated_attrs:
                        # There is a score update for this match, push a notification
                        logging.info("Sending push notifications for {}".format(match.key_name))
                        try:
                            NotificationHelper.send_match_score_update(match)
                        except Exception, exception:
                            logging.error("Error sending match updates: {}".format(exception))
                            logging.error(traceback.format_exc())
                        try:
                            TBANSHelper.match_score(match)
                        except Exception, exception:
                            logging.error("Error sending match {} updates: {}".format(match.key_name, exception))
                            logging.error(traceback.format_exc())
                else:
                    if is_new or (set(['alliances_json', 'time', 'time_string']).intersection(set(updated_attrs)) != set()):
                        # The match has not been played and we're changing a property that affects the event's schedule
                        # So send a schedule update notification for the parent event
                        if event not in unplayed_match_events:
                            unplayed_match_events.append(event)

            # Try to send video notifications
            if '_video_added' in updated_attrs:
                try:
                    NotificationHelper.send_match_video(match)
                except Exception, exception:
                    logging.error("Error sending match video updates: {}".format(exception))
                    logging.error(traceback.format_exc())
                try:
                    TBANSHelper.match_video(match)
                except Exception, exception:
                    logging.error("Error sending match video updates: {}".format(exception))
                    logging.error(traceback.format_exc())

        '''
        If we have an unplayed match during an event within a day, send out a schedule update notification
        '''
        for event in unplayed_match_events:
            try:
                logging.info("Sending schedule updates for: {}".format(event.key_name))
                NotificationHelper.send_schedule_update(event)
            except Exception, exception:
                logging.error("Eror sending schedule updates for: {}".format(event.key_name))
            try:
                TBANSHelper.event_schedule(event)
            except Exception, exception:
                logging.error("Eror sending schedule updates for: {}".format(event.key_name))
                logging.error(traceback.format_exc())
            try:
                # When an event gets a new schedule, we should schedule `match_upcoming` notifications for the first matches for the event
                TBANSHelper.schedule_upcoming_matches(event)
            except Exception, exception:
                logging.error("Eror scheduling match_upcoming for: {}".format(event.key_name))
                logging.error(traceback.format_exc())

        '''
        Enqueue firebase push
        '''
        affected_stats_event_keys = set()
        for (match, updated_attrs, is_new) in zip(matches, updated_attr_list, is_new_list):
            # Only attrs that affect stats
            if is_new or set(['alliances_json', 'score_breakdown_json']).intersection(set(updated_attrs)) != set():
                affected_stats_event_keys.add(match.event.id())
            try:
                FirebasePusher.update_match(match, updated_attrs)
            except Exception:
                logging.warning("Firebase update_match failed!")
                logging.warning(traceback.format_exc())

        # Enqueue statistics
        for event_key in affected_stats_event_keys:
            # Enqueue task to calculate matchstats
            try:
                taskqueue.add(
                    url='/tasks/math/do/event_matchstats/' + event_key,
                    method='GET')
            except Exception:
                logging.error("Error enqueuing event_matchstats for {}".format(event_key))
                logging.error(traceback.format_exc())

            # Enqueue task to calculate district points
            try:
                taskqueue.add(
                    url='/tasks/math/do/district_points_calc/{}'.format(event_key),
                    method='GET')
            except Exception:
                logging.error("Error enqueuing district_points_calc for {}".format(event_key))
                logging.error(traceback.format_exc())

            # Enqueue task to calculate event team status
            try:
                taskqueue.add(
                    url='/tasks/math/do/event_team_status/{}'.format(event_key),
                    method='GET')
            except Exception:
                logging.error("Error enqueuing event_team_status for {}".format(event_key))
                logging.error(traceback.format_exc())

            # Enqueue updating playoff advancement
            try:
                taskqueue.add(
                    url='/tasks/math/do/playoff_advancement_update/{}'.format(event_key),
                    method='GET')
            except Exception:
                logging.error("Error enqueuing advancement update for {}".format(event_key))
                logging.error(traceback.format_exc())
    """

    @classmethod
    def updateMerge(
        cls, new_match: Match, old_match: Match, auto_union: bool = True
    ) -> Match:

        # Lets postUpdateHook know if videos went from 0 to >0
        added_video = not old_match.has_video and new_match.has_video

        cls._update_attrs(new_match, old_match, auto_union)

        if added_video:
            old_match._updated_attrs.append("_video_added")

        return old_match
