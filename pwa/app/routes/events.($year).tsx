import { useState } from 'react';
import { InView } from 'react-intersection-observer';
import { useLoaderData, useNavigate } from 'react-router';

import { Event, getEventsByYear } from '~/api/tba/read';
import EventListTable from '~/components/tba/eventListTable';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import {
  TableOfContentsItem,
  TableOfContentsLink,
  TableOfContentsList,
} from '~/components/ui/toc';
import { CMP_EVENT_TYPES, EventType } from '~/lib/api/EventType';
import { getEventWeekString, sortEventsComparator } from '~/lib/eventUtils';
import {
  VALID_YEARS,
  parseParamsForYearElseDefault,
  pluralize,
  slugify,
} from '~/lib/utils';

import { Route } from '.react-router/types/app/routes/+types/events.($year)';

async function loadData(params: Route.LoaderArgs['params']) {
  const year = await parseParamsForYearElseDefault(params);
  if (year === undefined) {
    throw new Response(null, {
      status: 404,
    });
  }

  const events = await getEventsByYear({ path: { year } });

  if (events.data === undefined) {
    throw new Response(null, {
      status: 500,
    });
  }

  if (events.data.length === 0) {
    throw new Response(null, {
      status: 404,
    });
  }

  return { year, events: events.data };
}

export async function loader({ params }: Route.LoaderArgs) {
  return await loadData(params);
}

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return await loadData(params);
}

export function meta({ data }: Route.MetaArgs) {
  return [
    {
      title: `${data.year} FIRST Robotics Events - The Blue Alliance`,
    },
    {
      name: 'description',
      content: `Event list for the ${data.year} FIRST Robotics Competition.`,
    },
  ];
}

interface EventGroup {
  groupName: string;
  slug: string;
  events: Event[];
}

function groupBySections(events: Event[]): EventGroup[] {
  const eventsByWeek = new Map<string, EventGroup>();
  const eventsByChampionship = new Map<string, EventGroup>();
  const FOCEvents: EventGroup = {
    groupName: 'FIRST Festival of Champions',
    slug: 'foc',
    events: [],
  };
  const preaseasonEvents: EventGroup = {
    groupName: 'Preseason',
    slug: 'preaseason',
    events: [],
  };
  const offseasonEvents: EventGroup = {
    groupName: 'Offseason',
    slug: 'offseason',
    events: [],
  };
  events.forEach((event) => {
    // Events by week
    const weekStr = getEventWeekString(event);
    if (weekStr != null) {
      const weekGroup = eventsByWeek.get(weekStr);
      if (weekGroup) {
        weekGroup.events.push(event);
      } else {
        eventsByWeek.set(weekStr, {
          groupName: weekStr,
          slug: slugify(weekStr),
          events: [event],
        });
      }
    }

    // Events by Championship
    if (CMP_EVENT_TYPES.has(event.event_type)) {
      const groupName =
        event.year >= 2017 && event.year <= 2020
          ? `FIRST Championship - ${event.city}`
          : 'FIRST Championship';
      const championshipGroup = eventsByChampionship.get(groupName);
      if (championshipGroup) {
        championshipGroup.events.push(event);
      } else {
        eventsByChampionship.set(groupName, {
          groupName,
          slug: slugify(groupName),
          events: [event],
        });
      }
    }

    // FOC
    if (event.event_type === EventType.FOC) {
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
  const [inView, setInView] = useState(new Set());
  const navigate = useNavigate();

  const sortedEvents = events.sort(sortEventsComparator);
  const groupedEvents = groupBySections(sortedEvents);

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <div className="basis-full lg:basis-1/6">
        <div className="sticky top-14 pt-8">
          <Select
            value={String(year)}
            onValueChange={(value) => {
              void navigate(`/events/${value}`);
            }}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder={year} />
            </SelectTrigger>
            <SelectContent>
              {VALID_YEARS.map((y) => (
                <SelectItem key={y} value={`${y}`}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <TableOfContentsList className="mt-2">
            {groupedEvents.map((group) => (
              <TableOfContentsItem key={group.slug}>
                <TableOfContentsLink
                  to={`#${group.slug}`}
                  replace={true}
                  isActive={inView.has(group.slug)}
                >
                  {group.groupName}
                </TableOfContentsLink>
              </TableOfContentsItem>
            ))}
          </TableOfContentsList>
        </div>
      </div>
      <div className="basis-full py-8 lg:basis-5/6">
        <h1 className="mb-3 text-3xl font-medium">
          {year} <em>FIRST</em> Robotics Competition Events{' '}
          <small className="text-xl text-slate-500">
            {events.length} Events
          </small>
        </h1>
        {groupedEvents.map((group) => (
          <div key={group.slug} id={group.slug}>
            <InView
              as="div"
              onChange={(inView) => {
                setInView((prev) => {
                  if (inView) {
                    prev.add(group.slug);
                  } else {
                    prev.delete(group.slug);
                  }
                  return new Set(prev);
                });
              }}
            >
              <h2 className="mt-5 text-2xl">
                {group.groupName}{' '}
                <small className="text-slate-500">
                  {pluralize(group.events.length, 'Event', 'Events')}
                </small>
              </h2>
              <EventListTable events={group.events} />
            </InView>
          </div>
        ))}
      </div>
    </div>
  );
}
