import { useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';

import { getEventsByYearOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import EventListTable from '~/components/tba/eventListTable';
import { getCurrentWeekEvents } from '~/lib/eventUtils';
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
  const { currentSeason } = Route.useRouteContext();
  const { data: events } = useSuspenseQuery(
    getEventsByYearOptions({ path: { year: currentSeason } }),
  );
  const weekEvents = getCurrentWeekEvents(events);

  return (
    <div>
      <h1 className="mt-5 mb-2.5 text-4xl">This Week&apos;s Events</h1>
      {weekEvents.length > 0 ? (
        <EventListTable events={weekEvents} enableGrouping />
      ) : (
        <p className="text-muted-foreground">No events this week.</p>
      )}
    </div>
  );
}
