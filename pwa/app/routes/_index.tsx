import type { MetaFunction } from '@remix-run/node';
import { json, useLoaderData } from '@remix-run/react';
import { getEventsByYear, getStatus } from '~/api/v3';

export async function loader() {
  const status = await getStatus({});

  if (status.status !== 200) {
    throw new Response(null, {
      status: 500,
    });
  }

  const year = status.data.current_season;
  const events = await getValidEvents(year);

  return json({
    status: status.data,
    events: events.data,
  });
}

export async function getValidEvents(year: number) {
  const events = await getEventsByYear({year});

  if (events.status !== 200) {
    throw new Response(null, {
      status: 500,
    })
  }

  if (events.data.length === 0) {
    throw new Response(null, {
      status: 404,
    });
  }

  return events;
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
    <div className="p-4 font-sans">
      <h1 className="text-3xl">The Blue Alliance</h1>
      <p>
        The Blue Alliance is the best way to scout, watch, and relive the{' '}
        <i>FIRST</i> Robotics Competition.
      </p>
      <p>Current Season: {status.current_season}</p>
      <p>Total Events: {events.length}</p>
      {events.map((event) => (
        <a href={event.event_code}>{event.name}</a>
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
