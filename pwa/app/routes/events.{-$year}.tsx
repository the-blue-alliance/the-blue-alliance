import { useSuspenseQuery } from '@tanstack/react-query';
import {
  createFileRoute,
  notFound,
  redirect,
  useNavigate,
} from '@tanstack/react-router';
import { cn } from 'cn';
import { useMemo, useState } from 'react';

import {
  getDistrictsByYearOptions,
  getEventsByYearOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import EventListTable from '~/components/tba/eventListTable';
import {
  TableOfContents,
  TableOfContentsSection,
  type TocNode,
} from '~/components/tba/tableOfContents';
import { YearSelector } from '~/components/tba/yearSelector';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import {
  type EventGroup,
  groupEventsBySections,
  sortEventsComparator,
} from '~/lib/eventUtils';
import { staleTimeForYear } from '~/lib/queryClient';
import {
  parseParamsForYearElseDefault,
  pluralize,
  publicCacheControlHeaders,
  useValidYears,
} from '~/lib/utils';

export const Route = createFileRoute('/events/{-$year}')({
  staticData: {
    // Drawn in the server-rendered TOC placeholder; mirrors the real bar below.
    tocPreview: ({ year }: { year: number }) => ({
      activeLabel: 'Week 1',
      action: <EventsTocActionsPreview year={year} />,
    }),
  },
  beforeLoad: ({ params }) => {
    if (params.year !== undefined && Number.isNaN(Number(params.year))) {
      throw redirect({
        to: '/district/$districtAbbreviation/{-$year}',
        params: { districtAbbreviation: params.year },
      });
    }
  },
  loader: async ({ params, context: { queryClient, currentSeason } }) => {
    const year = parseParamsForYearElseDefault(currentSeason, params);
    if (year === undefined) {
      throw notFound();
    }

    const yearStaleTime = staleTimeForYear(year);
    await Promise.all([
      queryClient.ensureQueryData({
        ...getEventsByYearOptions({ path: { year } }),
        staleTime: yearStaleTime,
      }),
      queryClient.ensureQueryData({
        ...getDistrictsByYearOptions({ path: { year } }),
        staleTime: yearStaleTime,
      }),
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
}); // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop

const compactTriggerClassName = `max-lg:h-8 max-lg:w-auto max-lg:border-none
  max-lg:px-2 max-lg:text-foreground max-lg:hover:bg-accent`;

function EventsTocActionsPreview({ year }: { year: number }) {
  return (
    <div className="flex items-center gap-1">
      <YearSelector
        currentLabel={String(year)}
        triggerClassName={compactTriggerClassName}
        options={[]}
      />
      <Select
        items={[{ value: 'all', label: 'All Events' }]}
        defaultValue="all"
      >
        <SelectTrigger className={cn(compactTriggerClassName, 'gap-2')}>
          <SelectValue />
        </SelectTrigger>
      </Select>
    </div>
  );
}

function YearEventsPage() {
  const { year } = Route.useLoaderData();
  const yearStaleTime = staleTimeForYear(year);
  const { data: events } = useSuspenseQuery({
    ...getEventsByYearOptions({ path: { year } }),
    staleTime: yearStaleTime,
  });
  const { data: districts } = useSuspenseQuery({
    ...getDistrictsByYearOptions({ path: { year } }),
    staleTime: yearStaleTime,
  });
  const validYears = useValidYears();
  const [inView, setInView] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  const sortedEvents = events.toSorted(sortEventsComparator);
  const groupedEvents = groupEventsBySections(sortedEvents);
  const officialGroups = groupedEvents.filter((group) => group.isOfficial);
  const unofficialGroups = groupedEvents.filter((group) => !group.isOfficial);
  const officialEventCount = officialGroups.reduce(
    (acc, group) => acc + group.events.length,
    0,
  );

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

  // Base UI's Select.Value renders the raw value unless the items are
  // registered on Select.Root, so provide value -> label pairs there too.
  const districtItems = [
    { value: 'all', label: 'All Events' },
    ...(year >= 2025 ? [{ value: 'regional', label: 'Regional Events' }] : []),
    ...districts
      .slice()
      .sort((a, b) => a.display_name.localeCompare(b.display_name))
      .map((district) => ({
        value: district.abbreviation,
        label: district.display_name,
      })),
  ];

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <TableOfContents tocItems={tocItems} inView={inView}>
        <div className="flex items-center gap-1 lg:flex-col lg:gap-2">
          <YearSelector
            currentLabel={String(year)}
            triggerClassName={compactTriggerClassName}
            options={validYears.map((y) => ({
              label: String(y),
              to: `/events/${y}`,
              isCurrent: y === year,
            }))}
          />
          <Select
            items={districtItems}
            defaultValue="all"
            onValueChange={(value) => {
              if (value === 'regional') {
                void navigate({ to: `/events/regional/${year}` });
              } else if (value !== 'all') {
                void navigate({ to: `/district/${value}/${year}` });
              }
            }}
          >
            <SelectTrigger className={cn(compactTriggerClassName, 'gap-2')}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent align="start">
              {districtItems.map(({ value, label }) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </TableOfContents>
      <div className="basis-full lg:basis-5/6">
        <h1 className="mb-1 text-2xl font-medium md:text-3xl">
          {year} <i>FIRST</i> Robotics Competition Events{' '}
          <small
            className="block text-base font-normal text-muted-foreground
              md:inline md:text-xl"
          >
            {events.length} events ({officialEventCount} official)
          </small>
        </h1>
        {officialGroups.length > 0 && (
          <div id="official">
            {officialGroups.map((group) => (
              <EventGroupSection
                key={group.slug}
                group={group}
                setInView={setInView}
              />
            ))}
          </div>
        )}
        {unofficialGroups.length > 0 && (
          <>
            <h2
              id="unofficial"
              className="mt-3 text-xl font-medium md:text-2xl"
            >
              Unofficial Events{' '}
              <small className="text-base font-normal text-muted-foreground">
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
      <h2 className="mt-2 text-lg font-medium md:text-xl">
        {group.groupName}{' '}
        <small className="text-sm font-normal text-muted-foreground">
          {pluralize(group.events.length, 'Event', 'Events')}
        </small>
      </h2>
      <EventListTable events={group.events} />
    </TableOfContentsSection>
  );
}
