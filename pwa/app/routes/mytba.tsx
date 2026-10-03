import { useQuery, useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';

import { listFavorites } from '~/api/tba/mobile/sdk.gen';
import type { Event } from '~/api/tba/read';
import {
  getEventsByYearOptions,
  getStatusOptions,
  getTeamEventsByYearOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { useAuth } from '~/components/tba/auth/auth';
import LoginPage from '~/components/tba/auth/loginPage';
import EventListTable from '~/components/tba/eventListTable';
import { TeamLink } from '~/components/tba/links';
import { Badge } from '~/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';
import { SEASON_EVENT_TYPES } from '~/lib/api/EventType';
import { isEventWithinDays, sortEvents } from '~/lib/eventUtils';
import { MODEL_TYPE, publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/mytba')({
  loader: async ({ context: { queryClient } }) => {
    const status = await queryClient.ensureQueryData(getStatusOptions({}));
    await queryClient.ensureQueryData(
      getEventsByYearOptions({
        path: { year: status?.current_season ?? new Date().getFullYear() },
      }),
    );
  },
  headers: publicCacheControlHeaders(),
  head: () => ({
    meta: [
      { title: 'myTBA Dashboard - The Blue Alliance' },
      {
        name: 'description',
        content: 'Track your favorite teams at the FIRST Robotics Competition.',
      },
    ],
  }),
  component: MyTBADashboard,
});

function MyTBADashboard() {
  const { isInitialLoading, user } = useAuth();

  if (isInitialLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <LoginPage />;
  }

  return <MyTBADashboardContent />;
}

function MyTBADashboardContent() {
  const { user } = useAuth();
  const { data: status } = useSuspenseQuery(getStatusOptions({}));
  const year = status?.current_season ?? new Date().getFullYear();

  const { data: favorites } = useQuery({
    queryKey: ['favorites', user?.uid],
    queryFn: async () => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const response = await listFavorites({ auth: token });
      return response.data;
    },
    enabled: !!user,
  });

  const favoriteTeamKeys =
    favorites?.favorites
      ?.filter((f) => f.model_type === MODEL_TYPE.TEAM)
      .map((f) => f.model_key) ?? [];

  // Fetch events for each favorited team
  const teamEventQueries = favoriteTeamKeys.map((teamKey) =>
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useQuery(
      getTeamEventsByYearOptions({
        path: { team_key: teamKey, year },
      }),
    ),
  );

  const now = new Date();

  // Build team → events mapping
  const teamEventsMap = new Map<string, Event[]>();
  favoriteTeamKeys.forEach((teamKey, i) => {
    const data = teamEventQueries[i]?.data;
    if (data) {
      teamEventsMap.set(teamKey, data);
    }
  });

  // Categorize teams by competition status
  const competing: { teamKey: string; events: Event[] }[] = [];
  const upcoming: { teamKey: string; events: Event[] }[] = [];
  const finished: { teamKey: string; events: Event[] }[] = [];

  for (const [teamKey, events] of teamEventsMap) {
    const seasonEvents = events.filter((e) =>
      SEASON_EVENT_TYPES.has(e.event_type),
    );
    const liveEvents = seasonEvents.filter((e) => isEventWithinDays(e, 0, 1));
    const futureEvents = seasonEvents.filter(
      (e) => new Date(e.start_date) > now,
    );
    const pastEvents = seasonEvents.filter((e) => new Date(e.end_date) < now);

    if (liveEvents.length > 0) {
      competing.push({ teamKey, events: liveEvents });
    } else if (futureEvents.length > 0) {
      upcoming.push({ teamKey, events: futureEvents });
    } else if (pastEvents.length > 0) {
      finished.push({ teamKey, events: pastEvents });
    }
  }

  if (favoriteTeamKeys.length === 0) {
    return (
      <div>
        <h1 className="mt-8 mb-4 text-4xl">myTBA Dashboard</h1>
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No favorite teams yet. Add teams to your favorites to see them here.
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <h1 className="mt-8 mb-4 text-4xl">myTBA Dashboard</h1>

      {competing.length > 0 && (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
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
              Currently Competing
            </CardTitle>
            <CardDescription>
              Your teams that are at events right now
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-3">
              {competing.map(({ teamKey, events }) => (
                <TeamEventCard
                  key={teamKey}
                  teamKey={teamKey}
                  events={events}
                  status="live"
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {upcoming.length > 0 && (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Upcoming</CardTitle>
            <CardDescription>
              Your teams with future events this season
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-3">
              {upcoming.map(({ teamKey, events }) => (
                <TeamEventCard
                  key={teamKey}
                  teamKey={teamKey}
                  events={events}
                  status="upcoming"
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {finished.length > 0 && (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Season Complete</CardTitle>
            <CardDescription>
              Your teams that have finished their season events
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-3">
              {finished.map(({ teamKey, events }) => (
                <TeamEventCard
                  key={teamKey}
                  teamKey={teamKey}
                  events={events}
                  status="finished"
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function TeamEventCard({
  teamKey,
  events,
  status,
}: {
  teamKey: string;
  events: Event[];
  status: 'live' | 'upcoming' | 'finished';
}) {
  const sortedEvents = sortEvents(events);

  return (
    <div className="rounded-lg border p-3">
      <div className="mb-2 flex items-center gap-2">
        <TeamLink
          teamOrKey={teamKey}
          className="text-lg font-semibold text-primary hover:underline"
        >
          Team {teamKey.substring(3)}
        </TeamLink>
        {status === 'live' && (
          <Badge variant="default" className="bg-green-600">
            Live
          </Badge>
        )}
      </div>
      <EventListTable events={sortedEvents} />
    </div>
  );
}
