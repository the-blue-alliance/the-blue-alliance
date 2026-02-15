import { useSuspenseQuery } from '@tanstack/react-query';
import { Link, createFileRoute } from '@tanstack/react-router';

import MdiVideo from '~icons/mdi/video';

import type { Event } from '~/api/tba/read';
import {
  getEventsByYearOptions,
  getStatusOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import EventListTable from '~/components/tba/eventListTable';
import InlineIcon from '~/components/tba/inlineIcon';
import { KickoffCountdown } from '~/components/tba/kickoffCountdown';
import { Button } from '~/components/ui/button';
import {
  CMP_EVENT_TYPES,
  EventType,
  SEASON_EVENT_TYPES,
} from '~/lib/api/EventType';
import {
  getCurrentWeekEvents,
  isEventWithinDays,
  sortEvents,
} from '~/lib/eventUtils';
import { publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/')({
  loader: async ({ context: { queryClient } }) => {
    const status = await queryClient.ensureQueryData(getStatusOptions({}));
    await queryClient.ensureQueryData(
      getEventsByYearOptions({
        path: { year: status?.current_season ?? new Date().getFullYear() },
      }),
    );
  },
  headers: publicCacheControlHeaders(),
  component: Home,
});

type SeasonPhase =
  | 'build-season'
  | 'competition'
  | 'championship'
  | 'offseason';

function detectSeasonPhase(events: Event[]): SeasonPhase {
  const now = new Date();
  const seasonEvents = events.filter((e) =>
    SEASON_EVENT_TYPES.has(e.event_type),
  );
  const cmpEvents = events.filter((e) => CMP_EVENT_TYPES.has(e.event_type));

  // Check if championship events are happening now
  const liveCmpEvents = cmpEvents.filter((e) => isEventWithinDays(e, 0, 1));
  if (liveCmpEvents.length > 0) {
    return 'championship';
  }

  // Check if competition events are happening this week
  const weekEvents = getCurrentWeekEvents(events);
  const competitionWeekEvents = weekEvents.filter((e) =>
    SEASON_EVENT_TYPES.has(e.event_type),
  );
  if (competitionWeekEvents.length > 0) {
    return 'competition';
  }

  // Check if season events haven't started yet
  const firstSeasonEvent = seasonEvents[0];
  if (firstSeasonEvent && new Date(firstSeasonEvent.start_date) > now) {
    return 'build-season';
  }

  // Check if there are future season events
  const futureSeasonEvents = seasonEvents.filter(
    (e) => new Date(e.end_date) >= now,
  );
  if (futureSeasonEvents.length > 0) {
    return 'competition';
  }

  return 'offseason';
}

function Home() {
  const { data: status } = useSuspenseQuery(getStatusOptions({}));
  const year = status?.current_season ?? new Date().getFullYear();
  const { data: events } = useSuspenseQuery(
    getEventsByYearOptions({ path: { year } }),
  );
  const weekEvents = getCurrentWeekEvents(events);
  const phase = detectSeasonPhase(events);

  return (
    <div>
      <div className="px-6 py-10 sm:py-16 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="mt-2 text-4xl font-bold tracking-tight sm:text-5xl">
            The Blue Alliance
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-lg leading-6">
            The Blue Alliance is the best way to scout, watch, and relive the{' '}
            <em>FIRST</em> Robotics Competition.
          </p>
        </div>
      </div>

      {phase === 'build-season' && (
        <BuildSeasonContent events={events} year={year} />
      )}

      {phase === 'competition' && (
        <CompetitionSeasonContent
          events={events}
          weekEvents={weekEvents}
          year={year}
        />
      )}

      {phase === 'championship' && (
        <ChampionshipContent events={events} year={year} />
      )}

      {phase === 'offseason' && (
        <OffseasonContent events={events} year={year} />
      )}
    </div>
  );
}

function BuildSeasonContent({
  events,
  year,
}: {
  events: Event[];
  year: number;
}) {
  // Hardcode kickoff for the current season
  const kickoffDate = new Date(`${year}-01-11T12:00:00-05:00`);

  const upcomingSeasonEvents = sortEvents(
    events.filter((e) => SEASON_EVENT_TYPES.has(e.event_type)).slice(0, 10),
  );

  return (
    <>
      <KickoffCountdown kickoffDateTimeEST={kickoffDate} />

      {upcomingSeasonEvents.length > 0 && (
        <div>
          <h2 className="mt-5 mb-2.5 text-3xl">Upcoming {year} Events</h2>
          <EventListTable events={upcomingSeasonEvents} />
          <div className="mt-2">
            <Button variant="outline" asChild>
              <Link to="/events/{-$year}" params={{ year: year.toString() }}>
                View all events
              </Link>
            </Button>
          </div>
        </div>
      )}
    </>
  );
}

function CompetitionSeasonContent({
  events,
  weekEvents,
  year,
}: {
  events: Event[];
  weekEvents: Event[];
  year: number;
}) {
  const liveEvents = weekEvents.filter(
    (e) => e.webcasts.length > 0 && isEventWithinDays(e, 0, 1),
  );

  // Get next week's events
  const now = new Date();
  const nextWeekStart = new Date(now);
  nextWeekStart.setDate(now.getDate() + (7 - now.getDay()));
  const nextWeekEnd = new Date(nextWeekStart);
  nextWeekEnd.setDate(nextWeekStart.getDate() + 7);

  const nextWeekEvents = sortEvents(
    events.filter((e) => {
      const startDate = new Date(e.start_date);
      return (
        SEASON_EVENT_TYPES.has(e.event_type) &&
        startDate >= nextWeekStart &&
        startDate < nextWeekEnd
      );
    }),
  );

  return (
    <>
      {liveEvents.length > 0 && (
        <div
          className="mb-4 rounded-lg border border-green-200 bg-green-50 p-4
            dark:border-green-900 dark:bg-green-950"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex size-3">
                <span
                  className="absolute inline-flex size-full animate-ping
                    rounded-full bg-green-400 opacity-75"
                />
                <span
                  className="relative inline-flex size-3 rounded-full
                    bg-green-500"
                />
              </span>
              <span className="font-semibold">
                {liveEvents.length} event{liveEvents.length !== 1 ? 's' : ''}{' '}
                live now
              </span>
            </div>
            <Button variant="success" size="sm" asChild>
              <Link to="/gameday">
                <InlineIcon iconSize="large">
                  <MdiVideo />
                  Watch on GameDay
                </InlineIcon>
              </Link>
            </Button>
          </div>
        </div>
      )}

      {weekEvents.length > 0 && (
        <div>
          <h2 className="mt-5 mb-2.5 text-3xl">This Week&apos;s Events</h2>
          <EventListTable events={weekEvents} />
        </div>
      )}

      {nextWeekEvents.length > 0 && (
        <div>
          <h2 className="mt-5 mb-2.5 text-3xl">Next Week</h2>
          <EventListTable events={nextWeekEvents} />
        </div>
      )}

      <div className="mt-2">
        <Button variant="outline" asChild>
          <Link to="/events/{-$year}" params={{ year: year.toString() }}>
            View all {year} events
          </Link>
        </Button>
      </div>
    </>
  );
}

function ChampionshipContent({
  events,
  year,
}: {
  events: Event[];
  year: number;
}) {
  const cmpEvents = sortEvents(
    events.filter((e) => CMP_EVENT_TYPES.has(e.event_type)),
  );
  const liveCmpEvents = cmpEvents.filter(
    (e) => e.webcasts.length > 0 && isEventWithinDays(e, 0, 1),
  );

  return (
    <>
      {liveCmpEvents.length > 0 && (
        <div
          className="mb-4 rounded-lg border border-green-200 bg-green-50 p-4
            dark:border-green-900 dark:bg-green-950"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex size-3">
                <span
                  className="absolute inline-flex size-full animate-ping
                    rounded-full bg-green-400 opacity-75"
                />
                <span
                  className="relative inline-flex size-3 rounded-full
                    bg-green-500"
                />
              </span>
              <span className="font-semibold">Championship is live!</span>
            </div>
            <Button variant="success" size="sm" asChild>
              <Link to="/gameday">
                <InlineIcon iconSize="large">
                  <MdiVideo />
                  Watch on GameDay
                </InlineIcon>
              </Link>
            </Button>
          </div>
        </div>
      )}

      <div>
        <h2 className="mt-5 mb-2.5 text-3xl">{year} Championship</h2>
        <EventListTable events={cmpEvents} />
      </div>
    </>
  );
}

function OffseasonContent({ events, year }: { events: Event[]; year: number }) {
  const now = new Date();
  const upcomingOffseason = sortEvents(
    events.filter(
      (e) =>
        e.event_type === EventType.OFFSEASON && new Date(e.start_date) >= now,
    ),
  ).slice(0, 10);

  const nextKickoff = new Date(`${year + 1}-01-11T12:00:00-05:00`);

  return (
    <>
      <KickoffCountdown kickoffDateTimeEST={nextKickoff} />

      {upcomingOffseason.length > 0 && (
        <div>
          <h2 className="mt-5 mb-2.5 text-3xl">Upcoming Offseason Events</h2>
          <EventListTable events={upcomingOffseason} />
        </div>
      )}

      <div className="mt-2">
        <Button variant="outline" asChild>
          <Link to="/events/{-$year}" params={{ year: year.toString() }}>
            View all {year} events
          </Link>
        </Button>
      </div>
    </>
  );
}
