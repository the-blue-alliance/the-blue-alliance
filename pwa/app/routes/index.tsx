import { useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';

import {
  getEventsByYearOptions,
  getStatusOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import EventListTable from '~/components/tba/eventListTable';
import { getCurrentWeekEvents } from '~/lib/eventUtils';
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

function Home() {
  const { data: status } = useSuspenseQuery(getStatusOptions({}));
  const { data: events } = useSuspenseQuery(
    getEventsByYearOptions({
      path: { year: status?.current_season ?? new Date().getFullYear() },
    }),
  );
  const weekEvents = getCurrentWeekEvents(events);

  return (
    <div>
      {weekEvents.length > 0 && (
        <div>
          <h1 className="mt-5 mb-2.5 text-4xl">This Week&apos;s Events</h1>
          <EventListTable events={weekEvents} />
        </div>
      )}
    </div>
  );
}
