import { useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';

import {
  getEventsByYearOptions,
  getStatusOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import EventListTable from '~/components/tba/eventListTable';
import { KickoffCountdown } from '~/components/tba/kickoffCountdown';
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

  // Commit hash is string-replaced, so we need to ignore eslint and typescript errors.
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-expect-error
  const commitHash = __COMMIT_HASH__ as string;

  return (
    <div>
      <div className="px-6 py-10 sm:py-16 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2
            className="mt-2 text-4xl font-bold tracking-tight text-gray-900
              sm:text-5xl"
          >
            The Blue Alliance
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-lg leading-6 text-gray-600">
            The Blue Alliance is the best way to scout, watch, and relive the{' '}
            <em>FIRST</em> Robotics Competition.
          </p>
        </div>
      </div>

      <KickoffCountdown
        kickoffDateTimeEST={new Date('2026-01-10T12:00:00-05:00')}
      />

      {weekEvents.length > 0 && (
        <div>
          <h1 className="mt-5 mb-2.5 text-4xl">This Week&apos;s Events</h1>
          <EventListTable events={weekEvents} />
        </div>
      )}

      <a
        href={`https://github.com/the-blue-alliance/the-blue-alliance/commit/${commitHash}`}
        target="_blank"
        rel="noreferrer"
      >
        Commit: {commitHash}
      </a>
    </div>
  );
}
