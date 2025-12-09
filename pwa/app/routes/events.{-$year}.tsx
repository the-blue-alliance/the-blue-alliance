import { createFileRoute, notFound, useNavigate } from '@tanstack/react-router';
import { useMemo, useState } from 'react';

import { Event, getEventsByYear } from '~/api/tba/read';
import EventListTable from '~/components/tba/eventListTable';
import {
  TableOfContents,
  TableOfContentsSection,
} from '~/components/tba/tableOfContents';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import { CMP_EVENT_TYPES, EventType } from '~/lib/api/EventType';
import { getEventWeekString, sortEventsComparator } from '~/lib/eventUtils';
import {
  VALID_YEARS,
  parseParamsForYearElseDefault,
  pluralize,
  slugify,
} from '~/lib/utils';

export const Route = createFileRoute('/events/{-$year}')({
  loader: async ({ params }) => {
    const year = await parseParamsForYearElseDefault(params);
    if (year === undefined) {
      throw notFound();
    }

    const events = await getEventsByYear({ path: { year } });

    if (events.data === undefined) {
      throw new Error('Failed to load events');
    }

    if (events.data.length === 0) {
      throw notFound();
    }

    return { year, events: events.data };
  },
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [
          { title: 'FIRST Robotics Events - The Blue Alliance' },
          {
            name: 'description',
            content: 'Event list for the FIRST Robotics Competition.',
          },
        ],
      };
    }

    return {
      meta: [
        {
          title: `${loaderData.year} FIRST Robotics Events - The Blue Alliance`,
        },
        {
          name: 'description',
          content: `Event list for the ${loaderData.year} FIRST Robotics Competition.`,
        },
      ],
    };
  },
  component: YearEventsPage,
});

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

function YearEventsPage() {
  const { year, events } = Route.useLoaderData();
  const [inView, setInView] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  const sortedEvents = events.sort(sortEventsComparator);
  const groupedEvents = groupBySections(sortedEvents);
  const tocItems = useMemo(
    () =>
      groupedEvents.map((group) => ({
        slug: group.slug,
        label: group.groupName,
      })),
    [groupedEvents],
  );

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <TableOfContents tocItems={tocItems} inView={inView}>
        <Select
          value={String(year)}
          onValueChange={(value) => {
            void navigate({ to: `/events/${value}` });
          }}
        >
          <SelectTrigger
            className="w-[120px] max-lg:h-6 max-lg:w-24 max-lg:border-none"
          >
            <SelectValue placeholder={year} />
          </SelectTrigger>
          <SelectContent className="max-h-[30vh] overflow-y-auto">
            {VALID_YEARS.map((y) => (
              <SelectItem key={y} value={`${y}`}>
                {y}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </TableOfContents>
      <div className="basis-full py-8 lg:basis-5/6">
        <h1 className="mb-3 text-3xl font-medium">
          {year} <em>FIRST</em> Robotics Competition Events{' '}
          <small className="text-xl text-slate-500">
            {events.length} Events
          </small>
        </h1>
        {groupedEvents.map((group) => (
          <div key={group.slug} id={group.slug}>
            <TableOfContentsSection
              key={group.slug}
              id={group.slug}
              setInView={setInView}
            >
              <h2 className="mt-5 text-2xl">
                {group.groupName}{' '}
                <small className="text-slate-500">
                  {pluralize(group.events.length, 'Event', 'Events')}
                </small>
              </h2>
              <EventListTable events={group.events} />
            </TableOfContentsSection>
          </div>
        ))}
      </div>
    </div>
  );
}
