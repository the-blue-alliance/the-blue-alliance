import { useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';

import { getEventsByYear, getStatus } from '~/api/tba/read';
import {
  getEventsByYearOptions,
  getStatusOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import EventListTable from '~/components/tba/eventListTable';
import { KickoffCountdown } from '~/components/tba/kickoffCountdown';
import { getCurrentWeekEvents } from '~/lib/eventUtils';

export const Route = createFileRoute('/')({
  loader: async ({ context }) => {
    const status = await context.queryClient.ensureQueryData(
      getStatusOptions({}),
    );

    await context.queryClient.ensureQueryData(
      getEventsByYearOptions({ path: { year: status.current_season } }),
    );
  },
  component: Home,
});

function Home() {
  const statusQuery = useSuspenseQuery(getStatusOptions({}));
  const eventsQuery = useSuspenseQuery(
    getEventsByYearOptions({ path: { year: statusQuery.data.current_season } }),
  );
  const events = getCurrentWeekEvents(eventsQuery.data);

  // Commit hash is string-replaced, so we need to ignore eslint and typescript errors.
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-expect-error
  const commitHash = __COMMIT_HASH__ as string;

  return (
    <div>
      <div className="px-6 py-10 sm:py-8 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2
            className="mt-2 text-4xl font-bold tracking-tight text-gray-900
              sm:text-6xl"
          >
            The Blue Alliance
          </h2>
          <p className="mt-6 text-lg leading-5 text-gray-600">
            The Blue Alliance is the best way to scout, watch, and relive the{' '}
            <i>FIRST</i> Robotics Competition.{' '}
            <a href="http://www.firstinspires.org/">
              Learn More About <i>FIRST</i>
            </a>
          </p>
        </div>
      </div>

      <KickoffCountdown
        kickoffDateTimeEST={new Date('2026-01-10T12:00:00-05:00')}
      />

      {events.length > 0 && (
        <div>
          <h1 className="mt-5 mb-2.5 text-4xl">This Week&apos;s Events</h1>
          <EventListTable events={events} />
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
