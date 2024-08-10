import { json, LoaderFunctionArgs } from '@remix-run/node';
import {
  ClientLoaderFunctionArgs,
  Link,
  Params,
  useLoaderData,
} from '@remix-run/react';
import { getEventsByYear } from '~/api/v3';

async function loadData(params: Params) {
  // TODO: Handle cases where no year is provided
  if (params.year === undefined || !/^\d{4}$/.test(params.year || '')) {
    throw new Response(null, {
      status: 404,
    });
  }

  const year = parseInt(params.year);
  const events = await getEventsByYear({ year });

  return { year, events };
}

export async function loader({ params }: LoaderFunctionArgs) {
  return json(await loadData(params));
}

export async function clientLoader({ params }: ClientLoaderFunctionArgs) {
  return await loadData(params);
}

export default function YearEventsPage() {
  const { year, events } = useLoaderData<typeof loader>();

  return (
    <>
      <h1 className="mb-2.5 mt-5 text-4xl">
        {year} <i>FIRST</i> Robotics Competition Events
      </h1>
      {events.map((event) => (
        <div key={event.key}>
          <Link to={`/event/${event.key}`}>{event.name}</Link>
        </div>
      ))}
    </>
  );
}
