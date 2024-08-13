import { json, LoaderFunctionArgs } from '@remix-run/node';
import {
  ClientLoaderFunctionArgs,
  Link,
  Params,
  useLoaderData,
} from '@remix-run/react';
import { getEventsByYear, Event } from '~/api/v3';
import EventListTable from '~/components/tba/eventListTable';
import { sortEventsComparator } from '~/lib/utils';

async function loadData(params: Params) {
  // TODO: Handle cases where no year is provided
  if (params.year === undefined || !/^\d{4}$/.test(params.year || '')) {
    throw new Response(null, {
      status: 404,
    });
  }

  const year = parseInt(params.year);
  const events = await getEventsByYear({ year });

  if (events.status !== 200) {
    throw new Response(null, {
      status: 500,
    });
  }

  return { year, events: events.data };
}

export async function loader({ params }: LoaderFunctionArgs) {
  return json(await loadData(params));
}

export async function clientLoader({ params }: ClientLoaderFunctionArgs) {
  return await loadData(params);
}

type EventGroup = {
  groupName: string;
  events: Event[];
};

function groupByWeek(events: Event[]): EventGroup[] {
  const eventsByWeek: Map<number, EventGroup> = new Map();
  events.forEach((event) => {
    if (event.week == null) {
      return;
    }
    const weekGroup = eventsByWeek.get(event.week);
    if (weekGroup) {
      weekGroup.events.push(event);
    } else {
      eventsByWeek.set(event.week, {
        groupName: `Week ${event.week + 1}`,
        events: [event],
      });
    }
  });
  return Array.from(eventsByWeek.values());
}

export default function YearEventsPage() {
  const { year, events } = useLoaderData<typeof loader>();

  const sortedEvents = events.sort(sortEventsComparator);
  const eventsByWeek = groupByWeek(sortedEvents);

  return (
    <div className="flex flex-wrap gap-4 lg:flex-nowrap">
      <div className="basis-full lg:basis-1/6">TODO Year Picker & Sections</div>
      <div className="basis-full lg:basis-5/6">
        <h1 className="mb-2.5 mt-5 text-4xl">
          {year} <i>FIRST</i> Robotics Competition Events
        </h1>
        {eventsByWeek.map((group) => (
          <div key={group.groupName}>
            <h2 className="text-2xl mt-5">
              {group.groupName}{' '}
              <small className="text-slate-500">
                {group.events.length}{' '}
                {`Event${group.events.length > 1 ? 's' : ''}`}
              </small>
            </h2>
            <EventListTable events={group.events} />
          </div>
        ))}
      </div>
    </div>
  );
}
