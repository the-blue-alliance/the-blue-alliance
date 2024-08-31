import type { MetaFunction } from '@remix-run/node';
import { json, useLoaderData } from '@remix-run/react';

import { getEventsByYear, getStatus } from '~/api/v3';
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
  const { status, events } = useLoaderData<typeof loader>();

  // Commit hash is string-replaced, so we need to ignore eslint and typescript errors.
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-expect-error
  const commitHash = __COMMIT_HASH__ as string;

  return (
    <div>
      <div className="bg-white px-6 py-2 sm:py-8 lg:px-8">
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
          <div className="mx-auto mt-10 max-w-3xl lg:mx-0 lg:max-w-none">
            <div className="grid grid-cols-1 gap-x-8 gap-y-6 text-base font-semibold leading-5 text-white sm:grid-cols-2 md:flex lg:gap-x-10">
              <a href="/suggest/offseason">
                Add an Offseason Event <span aria-hidden="true">&rarr;</span>
              </a>
              <a href="/eventwizard">
                Add Offseason Event Data <span aria-hidden="true">&rarr;</span>
              </a>
              <a href="/add-data">
                Adding Data Overview <span aria-hidden="true">&rarr;</span>
              </a>
              <a href="https://github.com/the-blue-alliance">
                Hack on TBA<span aria-hidden="true">&rarr;</span>
              </a>
              <a href="/donate">
                Donate to TBA<span aria-hidden="true">&rarr;</span>
              </a>
            </div>
          </div>
        </div>
      </div>
      <h1 className="text-3xl">The Blue Alliance</h1>
      <p>
        The Blue Alliance is the best way to scout, watch, and relive the{' '}
        <i>FIRST</i> Robotics Competition.
      </p>
      <p>Current Season: {status.current_season}</p>
      <p>Total Events: {events.length}</p>
      {events.map((event) => (
        <a key={event.event_code} href={event.event_code}>
          {event.name}
        </a>
      ))}
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
