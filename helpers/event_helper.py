import json
import logging
import collections
import datetime
import re

from google.appengine.api import memcache
from google.appengine.ext import ndb

from consts.district_type import DistrictType
from consts.event_type import EventType

from models.district import District
from models.event import Event
from models.match import Match

CHAMPIONSHIP_EVENTS_LABEL = 'FIRST Championship'
TWO_CHAMPS_LABEL = 'FIRST Championship - {}'
FOC_LABEL = 'FIRST Festival of Champions'
WEEKLESS_EVENTS_LABEL = 'Other Official Events'
OFFSEASON_EVENTS_LABEL = 'Offseason'
PRESEASON_EVENTS_LABEL = 'Preseason'


class EventHelper(object):
    """
    Helper class for Events.
    """
    @classmethod
    def alliance_selections_to_points(self, event, multiplier, alliance_selections):
        team_points = {}
        try:
            if event.key.id() == "2015micmp":
                # Special case for 2015 Michigan District CMP, due to there being 16 alliances instead of 8
                # Uses max of 48 points and no multiplier
                # See 2015 Admin Manual, section 7.4.3.1
                # http://www.firstinspires.org/sites/default/files/uploads/resource_library/frc/game-and-season-info/archive/2015/AdminManual20150407.pdf
                for n, alliance in enumerate(alliance_selections):
                    team_points[alliance['picks'][0]] = int(48 - (1.5 * n))
                    team_points[alliance['picks'][1]] = int(48 - (1.5 * n))
                    team_points[alliance['picks'][2]] = int((n + 1) * 1.5)
                    n += 1
            else:
                for n, alliance in enumerate(alliance_selections):
                    n += 1
                    team_points[alliance['picks'][0]] = (17 - n) * multiplier
                    team_points[alliance['picks'][1]] = (17 - n) * multiplier
                    team_points[alliance['picks'][2]] = n * multiplier
        except Exception, e:
            # Log only if this matters
            if event.district_key is not None:
                logging.error("Alliance points calc for {} errored!".format(event.key.id()))
                logging.exception(e)

        return team_points

    @classmethod
    def groupByWeek(self, events):
        """
        Events should already be ordered by start_date
        """
        to_return = collections.OrderedDict()  # key: week_label, value: list of events

        weekless_events = []
        offseason_events = []
        preseason_events = []
        for event in events:
            if event.official and event.event_type_enum in {EventType.CMP_DIVISION, EventType.CMP_FINALS}:
                if event.year >= 2017:
                    champs_label = TWO_CHAMPS_LABEL.format(event.city)
                else:
                    champs_label = CHAMPIONSHIP_EVENTS_LABEL
                if champs_label in to_return:
                    to_return[champs_label].append(event)
                else:
                    to_return[champs_label] = [event]
            elif event.official and event.event_type_enum in {EventType.REGIONAL, EventType.DISTRICT, EventType.DISTRICT_CMP_DIVISION, EventType.DISTRICT_CMP}:
                if (event.start_date is None or
                   (event.start_date.month == 12 and event.start_date.day == 31)):
                    weekless_events.append(event)
                else:
                    label = event.week_str
                    if label in to_return:
                        to_return[label].append(event)
                    else:
                        to_return[label] = [event]
            elif event.event_type_enum == EventType.FOC:
                if FOC_LABEL in to_return:
                    to_return[FOC_LABEL].append(event)
                else:
                    to_return[FOC_LABEL] = [event]
            elif event.event_type_enum == EventType.PRESEASON:
                preseason_events.append(event)
            else:
                # everything else is an offseason event
                offseason_events.append(event)

        # Add weekless + other events last
        if weekless_events:
            to_return[WEEKLESS_EVENTS_LABEL] = weekless_events
        if preseason_events:
            to_return[PRESEASON_EVENTS_LABEL] = preseason_events
        if offseason_events:
            to_return[OFFSEASON_EVENTS_LABEL] = offseason_events

        return to_return

    @classmethod
    def distantFutureIfNoStartDate(self, event):
        if not event.start_date:
            return datetime.datetime(2177, 1, 1, 1, 1, 1)
        else:
            return event.time_as_utc(event.start_date)

    @classmethod
    def distantFutureIfNoEndDate(self, event):
        if not event.end_date:
            return datetime.datetime(2177, 1, 1, 1, 1, 1)
        else:
            return event.end_date

    @classmethod
    def calculateTeamAvgScoreFromMatches(self, team_key, matches):
        """
        Given a team_key and some matches, find the team's average qual and elim score
        """
        all_qual_scores = []
        all_elim_scores = []
        for match in matches:
            if match.has_been_played:
                for alliance in match.alliances.values():
                    if team_key in alliance['teams']:
                        if match.comp_level in Match.ELIM_LEVELS:
                            all_elim_scores.append(alliance['score'])
                        else:
                            all_qual_scores.append(alliance['score'])
                        break
        qual_avg = float(sum(all_qual_scores)) / len(all_qual_scores) if all_qual_scores != [] else None
        elim_avg = float(sum(all_elim_scores)) / len(all_elim_scores) if all_elim_scores != [] else None
        return qual_avg, elim_avg, all_qual_scores, all_elim_scores

    @classmethod
    def calculateTeamWLTFromMatches(self, team_key, matches):
        """
        Given a team_key and some matches, find the Win Loss Tie.
        """
        wlt = {"win": 0, "loss": 0, "tie": 0}

        for match in matches:
            if match.has_been_played and match.winning_alliance is not None:
                if match.winning_alliance == "":
                    wlt["tie"] += 1
                elif team_key in match.alliances[match.winning_alliance]["teams"]:
                    wlt["win"] += 1
                else:
                    wlt["loss"] += 1
        return wlt

    @classmethod
    def getTeamWLT(self, team_key, event):
        """
        Given a team_key, and an event, find the team's Win Loss Tie.
        """
        match_keys = Match.query(Match.event == event.key, Match.team_key_names == team_key).fetch(500, keys_only=True)
        return self.calculateTeamWLTFromMatches(team_key, ndb.get_multi(match_keys))

    @classmethod
    def getWeekEvents(self):
        """
        Get events this week
        In general, if an event is currently going on, it shows up in this query
        An event shows up in this query iff:
        a) The event is within_a_day
        OR
        b) The event.start_date is on or within 4 days after the closest Wednesday/Monday (pre-2020/post-2020)
        """
        event_keys = memcache.get('EventHelper.getWeekEvents():event_keys')
        if event_keys is not None:
            return ndb.get_multi(event_keys)

        today = datetime.datetime.today()

        # Make sure all events to be returned are within range
        two_weeks_of_events_keys_future = Event.query().filter(
          Event.start_date >= (today - datetime.timedelta(weeks=1))).filter(
          Event.start_date <= (today + datetime.timedelta(weeks=1))).order(
          Event.start_date).fetch_async(keys_only=True)

        events = []

        diff_from_week_start = 0 - today.weekday()
        closest_start_monday = today + datetime.timedelta(days=diff_from_week_start)

        two_weeks_of_event_futures = ndb.get_multi_async(two_weeks_of_events_keys_future.get_result())
        for event_future in two_weeks_of_event_futures:
            event = event_future.get_result()
            if event.within_a_day:
                events.append(event)
            else:
                offset = event.start_date.date() - closest_start_monday.date()
                if (offset == datetime.timedelta(0)) or (offset > datetime.timedelta(0) and offset < datetime.timedelta(weeks=1)):
                    events.append(event)

        EventHelper.sort_events(events)
        memcache.set('EventHelper.getWeekEvents():event_keys', [e.key for e in events], 60*60)
        return events

    @classmethod
    def getEventsWithinADay(self):
        event_keys = memcache.get('EventHelper.getEventsWithinADay():event_keys')
        if event_keys is not None:
            return ndb.get_multi(event_keys)

        events = filter(lambda e: e.within_a_day, self.getWeekEvents())
        memcache.set('EventHelper.getEventsWithinADay():event_keys', [e.key for e in events], 60*60)
        return events

    @classmethod
    def getShortName(self, name_str, district_code=None):
        """
        Extracts a short name like "Silicon Valley" from an event name like
        "Silicon Valley Regional sponsored by Google.org".

        See https://github.com/the-blue-alliance/the-blue-alliance-android/blob/master/android/src/test/java/com/thebluealliance/androidclient/test/helpers/EventHelperTest.java
        """
        district_keys = memcache.get('EventHelper.getShortName():district_keys')
        if not district_keys:
            codes = set([d.id()[4:].upper() for d in District.query().fetch(keys_only=True)])
            if district_code:
                codes.add(district_code.upper())
            if 'MAR' in codes:  # MAR renamed to FMA in 2019
                codes.add('FMA')
            if 'TX' in codes:  # TX and FIT used interchangeably
                codes.add('FIT')
            district_keys = '|'.join(codes)
        memcache.set('EventHelper.getShortName():district_keys', district_keys, 60*60)

        # 2015+ districts
        # Numbered events with no name
        re_string = '({}) District Event (#\d+)'.format(district_keys)
        match = re.match(re_string, name_str)
        if match:
            return '{} {}'.format(match.group(1).strip(), match.group(2).strip())
        # The rest
        re_string = '(?:{}) District -?(.+)'.format(district_keys)
        match = re.match(re_string, name_str)
        if match:
            partial = match.group(1).strip()
            match2 = re.sub(r'(?<=[\w\s])Event\s*(?:[\w\s]*$)?', '', partial)
            return match2.strip()

        # 2014- districts
        # district championships, other districts, and regionals
        name_str = re.sub(r'\s?Event','', name_str)
        match = re.match(r'\s*(?:MAR |PNW |)(?:FIRST Robotics|FRC|)(.+)(?:District|Regional|Region|Provincial|State|Tournament|FRC|Field)(?:\b)(?:[\w\s]+?(#\d*)*)?', name_str)

        if match:
            short = ''.join(match.groups(''))
            match = re.match(r'(.+)(?:FIRST Robotics|FRC)', short)
            if match:
                result = match.group(1).strip()
            else:
                result = short.strip()
            if result.startswith('FIRST'):
                result = result[5:]
            return result.strip()

        return name_str.strip()

    @classmethod
    def parseDistrictName(cls, district_name_str):
        district = DistrictType.names.get(district_name_str, DistrictType.NO_DISTRICT)

        # Fall back to checking abbreviations if needed
        return district if district != DistrictType.NO_DISTRICT else DistrictType.abbrevs.get(district_name_str, DistrictType.NO_DISTRICT)

    @classmethod
    def getDistrictEnumFromEventName(cls, event_name):
        for abbrev, district_type in DistrictType.abbrevs.items():
            if '{} district'.format(abbrev) in event_name.lower():
                return district_type

        for district_name, district_type in DistrictType.elasticsearch_names.items():
            if district_name in event_name:
                return district_type

        return DistrictType.NO_DISTRICT

    @classmethod
    def getDistrictKeyFromEventName(cls, event_name, year_districts_future):
        year_districts = year_districts_future.get_result()
        for district in year_districts:
            if '{} district'.format(
                    district.abbreviation) in event_name.lower():
                return district.key
            if district.display_name and '{} district'.format(
                    district.display_name.lower()) in event_name.lower():
                return district.key

            if district.elasticsearch_name:
                search_names = district.elasticsearch_name.split(",")
                for s in search_names:
                    if s and event_name.lower().startswith(s.lower()):
                        return district.key

        return None

    @classmethod
    def parseEventType(self, event_type_str):
        """
        Given an event_type_str from USFIRST, return the proper event type
        Examples:
        'Regional' -> EventType.REGIONAL
        'District' -> EventType.DISTRICT
        'District Championship' -> EventType.DISTRICT_CMP
        'MI FRC State Championship' -> EventType.DISTRICT_CMP
        'Championship Finals' -> EventType.CMP_FINALS
        'Championship' -> EventType.CMP_FINALS
        """
        event_type_str = event_type_str.lower()

        # Easy to parse
        if 'regional' in event_type_str:
            return EventType.REGIONAL
        elif 'offseason' in event_type_str:
            return EventType.OFFSEASON
        elif 'preseason' in event_type_str:
            return EventType.PRESEASON

        # Districts have multiple names
        if ('district' in event_type_str) or ('state' in event_type_str)\
           or ('region' in event_type_str) or ('qualif' in event_type_str):
            if 'championship' in event_type_str:
                if 'division' in event_type_str:
                    return EventType.DISTRICT_CMP_DIVISION
                return EventType.DISTRICT_CMP
            else:
                return EventType.DISTRICT

        # Everything else with 'champ' should be a Championship event
        if 'champ' in event_type_str:
            if 'division' in event_type_str:
                return EventType.CMP_DIVISION
            else:
                return EventType.CMP_FINALS

        # An event slipped through!
        logging.warn("Event type '{}' not recognized!".format(event_type_str))
        return EventType.UNLABLED

    @classmethod
    def sort_events(cls, events):
        """
        Sorts by start date then end date
        Sort is stable
        """
        events.sort(key=EventHelper.distantFutureIfNoStartDate)
        events.sort(key=EventHelper.distantFutureIfNoEndDate)

    @classmethod
    def is_2015_playoff(Cls, event_key):
        year = event_key[:4]
        event_short = event_key[4:]
        return year == '2015' and event_short not in {'cc', 'cacc', 'mttd'}

    @classmethod
    def remapteams_matches(cls, matches, remap_teams):
        """
        Remaps teams in matches
        Mutates in place
        """
        for match in matches:
            for old_team, new_team in remap_teams.items():
                # Update alliances
                for color in ['red', 'blue']:
                    for attr in ['teams', 'surrogates', 'dqs']:
                        for i, key in enumerate(match.alliances[color][attr]):
                            if key == old_team:
                                match.dirty = True
                                match.alliances[color][attr][i] = new_team
                                match.alliances_json = json.dumps(match.alliances)

                # Update team key names
                match.team_key_names = []
                for alliance in match.alliances:
                    match.team_key_names.extend(match.alliances[alliance].get('teams', None))

    @classmethod
    def remapteams_alliances(cls, alliance_selections, remap_teams):
        """
        Remaps teams in alliance selections
        Mutates in place
        """
        for row in alliance_selections:
            for choice in ['picks', 'declines']:
                for old_team, new_team in remap_teams.items():
                    for i, key in enumerate(row[choice]):
                        if key == old_team:
                            row[choice][i] = new_team

    @classmethod
    def remapteams_rankings(cls, rankings, remap_teams):
        """
        Remaps teams in rankings
        Mutates in place
        """
        for row in rankings:
            for old_team, new_team in remap_teams.items():
                if str(row[1]) == old_team[3:]:
                    row[1] = new_team[3:]

    @classmethod
    def remapteams_rankings2(cls, rankings2, remap_teams):
        """
        Remaps teams in rankings2
        Mutates in place
        """
        for ranking in rankings2:
            if ranking['team_key'] in remap_teams:
                ranking['team_key'] = remap_teams[ranking['team_key']]

    @classmethod
    def remapteams_awards(cls, awards, remap_teams):
        """
        Remaps teams in awards
        Mutates in place
        """
        for award in awards:
            new_recipient_json_list = []
            new_team_list = []
            # Compute new recipient list and team list
            for recipient in award.recipient_list:
                for old_team, new_team in remap_teams.items():
                    if str(recipient['team_number']) == old_team[3:]:
                        award.dirty = True
                        recipient['team_number'] = new_team[3:]

                new_recipient_json_list.append(json.dumps(recipient))
                new_team_list.append(ndb.Key('Team', 'frc{}'.format(recipient['team_number'])))

            # Update
            award.recipient_json_list = new_recipient_json_list
            award.team_list = new_team_list
