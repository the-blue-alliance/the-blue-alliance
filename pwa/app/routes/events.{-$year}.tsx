import { useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute, notFound, useNavigate } from '@tanstack/react-router';
import { useMemo, useState } from 'react';

import { Event } from '~/api/tba/read';
import { getEventsByYearOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import EventListTable from '~/components/tba/eventListTable';
import {
  TableOfContents,
  TableOfContentsSection,
  type TocNode,
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
  publicCacheControlHeaders,
  slugify,
} from '~/lib/utils';

export const Route = createFileRoute('/events/{-$year}')({
  loader: async ({ params, context: { queryClient } }) => {
    const year = await parseParamsForYearElseDefault(queryClient, params);
    if (year === undefined) {
      throw notFound();
    }

    await Promise.all([
      queryClient.ensureQueryData(getEventsByYearOptions({ path: { year } })),
    ]);

    return { year };
  },
  headers: publicCacheControlHeaders(),
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
  isOfficial: boolean;
}

function groupBySections(events: Event[]): EventGroup[] {
  const eventsByWeek = new Map<string, EventGroup>();
  const eventsByChampionship = new Map<string, EventGroup>();
  const unofficialEventsByMonth = new Map<string, EventGroup>();
  const FOCEvents: EventGroup = {
    groupName: 'FIRST Festival of Champions',
    slug: 'foc',
    events: [],
    isOfficial: true,
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
          isOfficial: true,
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
          isOfficial: true,
        });
      }
    }

    // FOC
    if (event.event_type === EventType.FOC) {
      FOCEvents.events.push(event);
    }

    // Group unofficial events by month
    if (
      event.event_type == EventType.PRESEASON ||
      event.event_type == EventType.OFFSEASON
    ) {
      const eventDate = new Date(event.start_date);
      const monthName = eventDate.toLocaleDateString('default', {
        month: 'long',
      });
      const offseasonGroup = unofficialEventsByMonth.get(monthName);
      if (offseasonGroup) {
        offseasonGroup.events.push(event);
      } else {
        unofficialEventsByMonth.set(monthName, {
          groupName: monthName,
          slug: slugify(monthName),
          events: [event],
          isOfficial: false,
        });
      }
    }
  });

  const groups = Array.from(eventsByWeek.values()).concat(
    Array.from(eventsByChampionship.values()),
  );
  if (FOCEvents.events.length > 0) {
    groups.push(FOCEvents);
  }
  if (unofficialEventsByMonth.size > 0) {
    groups.push(...Array.from(unofficialEventsByMonth.values()));
  }
  return groups;
}

function YearEventsPage() {
  const { year } = Route.useLoaderData();
  const { data: events } = useSuspenseQuery({
    ...getEventsByYearOptions({ path: { year } }),
  });
  const [inView, setInView] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  const sortedEvents = events.sort(sortEventsComparator);
  const groupedEvents = groupBySections(sortedEvents);
  const officialGroups = groupedEvents.filter((group) => group.isOfficial);
  const unofficialGroups = groupedEvents.filter((group) => !group.isOfficial);

  const tocItems = useMemo(() => {
    const tocNodes: TocNode[] = [];

    if (officialGroups.length > 0) {
      tocNodes.push({
        slug: 'official',
        label: 'Official',
        children: officialGroups.map((group) => ({
          slug: group.slug,
          label: group.groupName,
        })),
      });
    }

    if (unofficialGroups.length > 0) {
      tocNodes.push({
        slug: 'unofficial',
        label: 'Unofficial',
        children: unofficialGroups.map((group) => ({
          slug: group.slug,
          label: group.groupName,
        })),
      });
    }

    return tocNodes;
  }, [officialGroups, unofficialGroups]);

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
          {year} <i>FIRST</i> Robotics Competition Events{' '}
          <small className="text-xl text-muted-foreground">
            {events.length} Events
          </small>
        </h1>
        {officialGroups.length > 0 && (
          <>
            <h2
              id="official"
              className="mt-5 scroll-mt-12 text-3xl lg:scroll-mt-4"
            >
              Official Events{' '}
              <small className="text-xl text-muted-foreground">
                {officialGroups.reduce(
                  (acc, group) => acc + group.events.length,
                  0,
                )}{' '}
                Events
              </small>
            </h2>
            {officialGroups.map((group) => (
              <EventGroupSection
                key={group.slug}
                group={group}
                setInView={setInView}
              />
            ))}
          </>
        )}
        {unofficialGroups.length > 0 && (
          <>
            <h2
              id="unofficial"
              className="mt-5 scroll-mt-12 text-3xl lg:scroll-mt-4"
            >
              Unofficial Events{' '}
              <small className="text-xl text-muted-foreground">
                {unofficialGroups.reduce(
                  (acc, group) => acc + group.events.length,
                  0,
                )}{' '}
                Events
              </small>
            </h2>
            {unofficialGroups.map((group) => (
              <EventGroupSection
                key={group.slug}
                group={group}
                setInView={setInView}
              />
            ))}
          </>
        )}
      </div>
    </div>
  );
}

function EventGroupSection({
  group,
  setInView,
}: {
  group: EventGroup;
  setInView: React.Dispatch<React.SetStateAction<Set<string>>>;
}) {
  return (
    <TableOfContentsSection
      key={group.slug}
      id={group.slug}
      setInView={setInView}
    >
      <h2 className="mt-5 text-2xl">
        {group.groupName}{' '}
        <small className="text-muted-foreground">
          {pluralize(group.events.length, 'Event', 'Events')}
        </small>
      </h2>
      <EventListTable events={group.events} />
    </TableOfContentsSection>
  );
}
