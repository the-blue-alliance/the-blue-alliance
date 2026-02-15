import { useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';
import { useMemo } from 'react';

import { Event } from '~/api/tba/read';
import {
  getEventsByYearOptions,
  getStatusOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { EventLink, EventLocationLink } from '~/components/tba/links';
import { WebcastIcon } from '~/components/tba/socialBadges';
import { Badge } from '~/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';
import { getEventDateString, getEventWeekString } from '~/lib/eventUtils';
import { publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/webcasts')({
  loader: async ({ context: { queryClient } }) => {
    const status = await queryClient.ensureQueryData(getStatusOptions());
    const year = status.current_season;

    await queryClient.ensureQueryData(
      getEventsByYearOptions({ path: { year } }),
    );

    return { year };
  },
  headers: publicCacheControlHeaders(),
  head: () => ({
    meta: [
      { title: 'Live Webcasts - The Blue Alliance' },
      {
        name: 'description',
        content:
          'Watch live webcasts from FIRST Robotics Competition events on The Blue Alliance.',
      },
    ],
  }),
  component: WebcastsPage,
});

interface EventGroup {
  label: string;
  events: Event[];
}

function groupEventsByWeek(events: Event[]): EventGroup[] {
  const groups = new Map<string, EventGroup>();

  for (const event of events) {
    const weekStr = getEventWeekString(event) ?? 'Other';
    const existing = groups.get(weekStr);
    if (existing) {
      existing.events.push(event);
    } else {
      groups.set(weekStr, { label: weekStr, events: [event] });
    }
  }

  return Array.from(groups.values());
}

function WebcastsPage() {
  const { year } = Route.useLoaderData();
  const { data: allEvents } = useSuspenseQuery({
    ...getEventsByYearOptions({ path: { year } }),
  });

  const eventsWithWebcasts = useMemo(
    () => allEvents.filter((event) => event.webcasts.length > 0),
    [allEvents],
  );

  const now = useMemo(() => new Date(), []);

  const currentEvents = useMemo(
    () =>
      eventsWithWebcasts.filter((event) => {
        const start = new Date(event.start_date);
        const end = new Date(event.end_date);
        end.setDate(end.getDate() + 1);
        return now >= start && now <= end;
      }),
    [eventsWithWebcasts, now],
  );

  const upcomingEvents = useMemo(
    () =>
      eventsWithWebcasts.filter((event) => {
        const start = new Date(event.start_date);
        return start > now;
      }),
    [eventsWithWebcasts, now],
  );

  const pastEvents = useMemo(
    () =>
      eventsWithWebcasts.filter((event) => {
        const end = new Date(event.end_date);
        end.setDate(end.getDate() + 1);
        return end < now;
      }),
    [eventsWithWebcasts, now],
  );

  const upcomingGroups = groupEventsByWeek(upcomingEvents);
  const pastGroups = groupEventsByWeek(pastEvents).reverse();

  return (
    <div className="py-8">
      <h1 className="mb-4 text-3xl font-medium">
        {year} Webcasts{' '}
        <small className="text-xl text-muted-foreground">
          {eventsWithWebcasts.length} Events with Webcasts
        </small>
      </h1>

      {currentEvents.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-2xl font-medium">Live Now</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {currentEvents.map((event) => (
              <EventWebcastCard key={event.key} event={event} />
            ))}
          </div>
        </section>
      )}

      {upcomingGroups.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-2xl font-medium">Upcoming</h2>
          {upcomingGroups.map((group) => (
            <div key={group.label} className="mb-4">
              <h3 className="mb-2 text-lg font-medium text-muted-foreground">
                {group.label}
              </h3>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {group.events.map((event) => (
                  <EventWebcastCard key={event.key} event={event} />
                ))}
              </div>
            </div>
          ))}
        </section>
      )}

      {pastGroups.length > 0 && (
        <section>
          <h2 className="mb-3 text-2xl font-medium">Past</h2>
          {pastGroups.map((group) => (
            <div key={group.label} className="mb-4">
              <h3 className="mb-2 text-lg font-medium text-muted-foreground">
                {group.label}
              </h3>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {group.events.map((event) => (
                  <EventWebcastCard key={event.key} event={event} />
                ))}
              </div>
            </div>
          ))}
        </section>
      )}

      {eventsWithWebcasts.length === 0 && (
        <p className="text-muted-foreground">
          No events with webcasts found for {year}.
        </p>
      )}
    </div>
  );
}

function EventWebcastCard({ event }: { event: Event }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">
          <EventLink eventOrKey={event}>{event.name}</EventLink>
        </CardTitle>
        <CardDescription>
          <EventLocationLink event={event} hideUSA hideVenue />
          {event.week !== null && (
            <Badge variant="secondary" className="ml-2">
              Week {event.week + 1}
            </Badge>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-xs text-muted-foreground">
          {getEventDateString(event, 'short')}
        </div>
        <div className="mt-2 flex flex-wrap gap-1">
          {event.webcasts.map((webcast) => (
            <WebcastIcon key={webcast.channel} webcast={webcast} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
