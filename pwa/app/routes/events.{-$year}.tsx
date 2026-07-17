import { useSuspenseQuery } from '@tanstack/react-query';
import {
  createFileRoute,
  notFound,
  redirect,
  useNavigate,
} from '@tanstack/react-router';
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
import {
  parseParamsForYearElseDefault,
  pluralize,
  publicCacheControlHeaders,
  useValidYears,
} from '~/lib/utils';

export const Route = createFileRoute('/events/{-$year}')({
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

    await Promise.all([
      queryClient.ensureQueryData(getEventsByYearOptions({ path: { year } })),
      queryClient.ensureQueryData(
        getDistrictsByYearOptions({ path: { year } }),
      ),
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

function YearEventsPage() {
  const { year } = Route.useLoaderData();
  const { data: events } = useSuspenseQuery({
    ...getEventsByYearOptions({ path: { year } }),
  });
  const { data: districts } = useSuspenseQuery({
    ...getDistrictsByYearOptions({ path: { year } }),
  });
  const validYears = useValidYears();
  const [inView, setInView] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  const sortedEvents = events.sort(sortEventsComparator);
  const groupedEvents = groupEventsBySections(sortedEvents);
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

  // Base UI's Select.Value renders the raw value unless the items are
  // registered on Select.Root, so provide value -> label pairs there too.
  const districtItems = [
    { value: 'all', label: 'All Events' },
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
        <YearSelector
          currentLabel={String(year)}
          triggerClassName="w-[120px] max-lg:h-6 max-lg:w-24 max-lg:border-none"
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
            if (value !== 'all') {
              void navigate({ to: `/district/${value}/${year}` });
            }
          }}
        >
          <SelectTrigger
            className="w-[180px] max-lg:h-6 max-lg:w-36 max-lg:border-none"
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {districtItems.map(({ value, label }) => (
              <SelectItem key={value} value={value}>
                {label}
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
