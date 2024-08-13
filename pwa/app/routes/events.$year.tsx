import { json, LoaderFunctionArgs } from '@remix-run/node';
import {
  ClientLoaderFunctionArgs,
  Params,
  useLoaderData,
} from '@remix-run/react';
import { getEventsByYear, Event } from '~/api/v3';
import EventListTable from '~/components/tba/eventListTable';
import { CMP_EVENT_TYPES, EventType } from '~/lib/api/EventType';
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

function groupBySections(events: Event[]): EventGroup[] {
  // TODO: Handle 2021 remote events
  const eventsByWeek: Map<number, EventGroup> = new Map();
  const eventsByChampionship: Map<string, EventGroup> = new Map();
  const FOCEvents: EventGroup = {
    groupName: 'FIRST Festival of Champions',
    events: [],
  };
  const preaseasonEvents: EventGroup = { groupName: 'Preseason', events: [] };
  const offseasonEvents: EventGroup = { groupName: 'Offseason', events: [] };
  events.forEach((event) => {
    // Events by week
    if (event.week != null) {
      const weekGroup = eventsByWeek.get(event.week);
      if (weekGroup) {
        weekGroup.events.push(event);
      } else {
        eventsByWeek.set(event.week, {
          groupName: `Week ${event.week + 1}`,
          events: [event],
        });
      }
    }

    // Events by Championship
    if (CMP_EVENT_TYPES.has(event.event_type)) {
      const groupName =
        event.year >= 2017 && event.year <= 2022
          ? `FIRST Championship - ${event.city}`
          : 'FIRST Championship';
      const championshipGroup = eventsByChampionship.get(groupName);
      if (championshipGroup) {
        championshipGroup.events.push(event);
      } else {
        eventsByChampionship.set(groupName, {
          groupName,
          events: [event],
        });
      }
    }

    // FOC
    if (event.event_type == EventType.FOC) {
      FOCEvents.events.push(event);
    }

    // Preaseason
    if (event.event_type == EventType.PRESEASON) {
      preaseasonEvents.events.push(event);
    }

    // Offseason
    if (event.event_type == EventType.OFFSEASON) {
      offseasonEvents.events.push(event);
    }
  });

  const groups = Array.from(eventsByWeek.values()).concat(
    Array.from(eventsByChampionship.values()),
  );
  if (FOCEvents.events.length > 0) {
    groups.push(FOCEvents);
  }
  if (preaseasonEvents.events.length > 0) {
    groups.push(preaseasonEvents);
  }
  if (offseasonEvents.events.length > 0) {
    groups.push(offseasonEvents);
  }
  return groups;
}

export default function YearEventsPage() {
  const { year, events } = useLoaderData<typeof loader>();

  const sortedEvents = events.sort(sortEventsComparator);
  const groupedEvents = groupBySections(sortedEvents);

  return (
    <div className="flex flex-wrap gap-4 lg:flex-nowrap">
      <div className="basis-full lg:basis-1/6">TODO Year Picker & Sections</div>
      <div className="basis-full lg:basis-5/6">
        <h1 className="mb-2.5 mt-5 text-4xl">
          {year} <i>FIRST</i> Robotics Competition Events
        </h1>
        {groupedEvents.map((group) => (
          <div key={group.groupName}>
            <h2 className="mt-5 text-2xl">
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
