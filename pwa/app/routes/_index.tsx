import type { MetaFunction } from '@remix-run/node';
import { json, useLoaderData } from '@remix-run/react';

import { getEventsByYear, getStatus } from '~/api/v3';
import EventListTable from '~/components/tba/eventListTable';
import { getCurrentWeekEvents } from '~/lib/eventUtils';

export async function loader() {
  const status = await getStatus({});

  if (status.status !== 200) {
    throw new Response(null, {
      status: 500,
    });
  }

  const events = await getValidEvents(status.data.current_season);

  return json({
    status: status.data,
    events: events,
  });
}

export async function getValidEvents(year: number) {
  const events = await getEventsByYear({ year });

  if (events.status !== 200) {
    throw new Response(null, {
      status: 500,
    });
  }

  if (events.data.length === 0) {
    throw new Response(null, {
      status: 404,
    });
  }

  const filteredEvents = getCurrentWeekEvents(events.data);

  return filteredEvents;
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
          <h2 className="mt-2 text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
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

      <h1 className="mb-2.5 mt-5 text-4xl">This Week&apos;s Events</h1>
      <EventListTable events={events} />
    </div>
  );
}
