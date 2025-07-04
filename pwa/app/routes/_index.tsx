import type { MetaFunction } from 'react-router';
import { useLoaderData } from 'react-router';

import { getEventsByYear, getStatus } from '~/api/tba/read';
import EventListTable from '~/components/tba/eventListTable';
import { getCurrentWeekEvents } from '~/lib/eventUtils';

export async function loader() {
  const status = await getStatus();

  if (status.data === undefined) {
    throw new Response(null, {
      status: 500,
    });
  }

  const year = status.data.current_season;
  const events = await getEventsByYear({ path: { year } });

  if (events.data === undefined) {
    throw new Response(null, {
      status: 500,
    });
  }

  const filteredEvents = getCurrentWeekEvents(events.data);

  return {
    events: filteredEvents,
  };
}

export const meta: MetaFunction = () => {
  return [
    { title: 'The Blue Alliance' },
    {
      name: 'description',
      content:
        'Team information and match videos and results from the FIRST Robotics Competition',
    },
  ];
};

export default function Index() {
  const { events } = useLoaderData<typeof loader>();

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

      {events.length > 0 ? (
        <div>
          <h1 className="mt-5 mb-2.5 text-4xl">This Week&apos;s Events</h1>
          <EventListTable events={events} />
        </div>
      ) : (
        <h1 className="mt-5 mb-2.5 text-4xl">No Events This Week</h1>
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
