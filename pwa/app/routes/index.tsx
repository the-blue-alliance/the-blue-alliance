import { useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';
import { Temporal } from 'temporal-polyfill';

import { getEventsByYearOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import EventListTable from '~/components/tba/eventListTable';
import { KickoffCountdown } from '~/components/tba/kickoffCountdown';
import { getCurrentWeekEvents } from '~/lib/eventUtils';
import { getKickoffCountdownTarget } from '~/lib/kickoffUtils';
import { publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/')({
  loader: async ({ context: { queryClient, currentSeason } }) => {
    await queryClient.ensureQueryData(
      getEventsByYearOptions({ path: { year: currentSeason } }),
    );
  },
  headers: publicCacheControlHeaders(),
  component: Home,
});

function Home() {
  const { currentSeason, status } = Route.useRouteContext();
  const { data: events } = useSuspenseQuery(
    getEventsByYearOptions({ path: { year: currentSeason } }),
  );
  const weekEvents = getCurrentWeekEvents(events);
  const kickoff = getKickoffCountdownTarget(
    status.kickoff_datetime,
    Temporal.Now.instant(),
  );

  return (
    <div>
      {kickoff !== null && (
        <div className="mt-5">
          <KickoffCountdown kickoffDateTimeEST={kickoff} />
        </div>
      )}

      <h1 className="mt-5 mb-2.5 text-4xl">This Week&apos;s Events</h1>
      {weekEvents.length > 0 ? (
        <EventListTable events={weekEvents} />
      ) : (
        <p className="text-muted-foreground">No events this week.</p>
      )}
    </div>
  );
}
