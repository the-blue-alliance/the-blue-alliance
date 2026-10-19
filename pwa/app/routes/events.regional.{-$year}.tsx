import { createFileRoute, notFound } from '@tanstack/react-router';
import { useState } from 'react';

import { RegionalAdvancement, RegionalRanking } from '~/api/tba/read';
import {
  getEventsByYearOptions,
  getRegionalAdvancementOptions,
  getRegionalRankingsOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { DataTable, TbaColumnDef } from '~/components/tba/dataTable';
import { EventLink } from '~/components/tba/links';
import { TeamLinkWithTooltip } from '~/components/tba/teamTooltip';
import { YearSelector } from '~/components/tba/yearSelector';
import { Badge } from '~/components/ui/badge';
import { Button } from '~/components/ui/button';
import { Input } from '~/components/ui/input';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import { staleTimeForYear } from '~/lib/queryClient';
import {
  doThrowNotFound,
  parseParamsForYearElseDefault,
  publicCacheControlHeaders,
  useValidYears,
} from '~/lib/utils';

const FIRST_REGIONAL_POOL_YEAR = 2025;

export const Route = createFileRoute('/events/regional/{-$year}')({
  loader: async ({ params, context: { queryClient, currentSeason } }) => {
    const year = parseParamsForYearElseDefault(currentSeason, params);
    if (year === undefined || year < FIRST_REGIONAL_POOL_YEAR) {
      throw notFound();
    }

    const staleTime = staleTimeForYear(year);
    const [rankings, advancement, events] = await Promise.all([
      queryClient
        .ensureQueryData({
          ...getRegionalRankingsOptions({ path: { year } }),
          staleTime,
        })
        .catch(doThrowNotFound),
      queryClient
        .ensureQueryData({
          ...getRegionalAdvancementOptions({ path: { year } }),
          staleTime,
        })
        .catch(() => null),
      queryClient
        .ensureQueryData({
          ...getEventsByYearOptions({ path: { year } }),
          staleTime,
        })
        .catch(() => []),
    ]);

    if (rankings === null) {
      throw notFound();
    }

    return {
      year,
      rankings,
      advancement,
      eventNames: Object.fromEntries(
        events.map((event) => [event.key, event.short_name || event.name]),
      ),
    };
  },
  headers: publicCacheControlHeaders(),
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [
          { title: 'Regional Championship Pool Rankings - The Blue Alliance' },
          {
            name: 'description',
            content:
              'Regional Championship pool rankings for the FIRST Robotics Competition.',
          },
        ],
      };
    }

    return {
      meta: [
        {
          title: `${loaderData.year} Regional Championship Pool Rankings - The Blue Alliance`,
        },
        {
          name: 'description',
          content: `Regional Championship pool rankings for the ${loaderData.year} FIRST Robotics Competition.`,
        },
      ],
    };
  },
  component: RegionalRankingsPage,
}); // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop

function RegionalRankingsPage() {
  const { year, rankings, advancement, eventNames } = Route.useLoaderData();
  const validYears = useValidYears().filter(
    (y) => y >= FIRST_REGIONAL_POOL_YEAR,
  );
  const [teamFilter, setTeamFilter] = useState('');
  const [notQualifiedOnly, setNotQualifiedOnly] = useState(false);

  const visibleRankings = rankings.filter(
    (ranking) =>
      ranking.team_key.substring(3).includes(teamFilter.trim()) &&
      !(notQualifiedOnly && advancement?.[ranking.team_key]?.cmp),
  );
  const hasSingleEventBonus = rankings.some(
    (r) => (r.event_points?.length ?? 0) < 2 && (r.single_event_bonus ?? 0) > 0,
  );

  const columns: TbaColumnDef<RegionalRanking>[] = [
    { header: 'Rank', size: 70, accessorFn: (ranking) => ranking.rank },
    {
      header: 'Team',
      size: 100,
      accessorFn: (ranking) => Number(ranking.team_key.substring(3)),
      cell: (info) => (
        <TeamLinkWithTooltip teamKey={info.row.original.team_key} year={year} />
      ),
    },
    {
      header: 'Event 1',
      size: 90,
      accessorFn: (ranking) => ranking.event_points?.[0]?.total ?? 0,
      cell: (info) => (
        <EventPoints
          points={info.row.original.event_points?.[0]}
          eventNames={eventNames}
        />
      ),
    },
    {
      header: 'Event 2',
      size: 90,
      accessorFn: (ranking) =>
        ranking.event_points?.[1]?.total ?? ranking.single_event_bonus ?? 0,
      cell: (info) => (
        <SecondEventPoints
          ranking={info.row.original}
          eventNames={eventNames}
        />
      ),
    },
    {
      header: 'Bonus',
      size: 90,
      accessorFn: (ranking) =>
        (ranking.rookie_bonus ?? 0) + (ranking.adjustments ?? 0),
      cell: (info) => info.getValue<number>() || '-',
    },
    {
      header: 'Total',
      size: 80,
      accessorFn: (ranking) => ranking.point_total,
      cell: (info) => (
        <span className="font-semibold">{info.getValue<number>()}</span>
      ),
    },
    {
      header: 'Qualified for CMP',
      size: 300,
      accessorFn: (ranking) => advancement?.[ranking.team_key]?.cmp_status,
      cell: (info) => (
        <AdvancementBadge
          advancement={advancement?.[info.row.original.team_key]}
          eventNames={eventNames}
        />
      ),
    },
  ];

  return (
    <div className="py-8">
      <div
        className="flex flex-col gap-4 sm:flex-row sm:items-start
          sm:justify-between"
      >
        <div>
          <h1 className="text-3xl font-medium">
            {year} Regional Pool Rankings
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Championship qualification for teams at regional events. Details on{' '}
            <a
              href="https://frc-events.firstinspires.org/ra/"
              target="_blank"
              rel="noreferrer"
            >
              firstinspires.org
            </a>
            .
          </p>
        </div>
        <YearSelector
          currentLabel={String(year)}
          triggerClassName="w-full sm:w-30"
          options={validYears.map((y) => ({
            label: String(y),
            to: `/events/regional/${y}`,
            isCurrent: y === year,
          }))}
        />
      </div>

      <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:items-center">
        <Input
          className="sm:max-w-60"
          inputMode="numeric"
          placeholder="Filter by team number"
          aria-label="Filter by team number"
          value={teamFilter}
          onChange={(e) => setTeamFilter(e.target.value)}
        />
        <fieldset className="flex gap-1" aria-label="Qualification">
          <Button
            size="sm"
            variant={notQualifiedOnly ? 'outline' : 'default'}
            aria-pressed={!notQualifiedOnly}
            onClick={() => setNotQualifiedOnly(false)}
          >
            All teams
          </Button>
          <Button
            size="sm"
            variant={notQualifiedOnly ? 'default' : 'outline'}
            aria-pressed={notQualifiedOnly}
            onClick={() => setNotQualifiedOnly(true)}
          >
            Not qualified
          </Button>
        </fieldset>
      </div>

      <div className="mt-2">
        <DataTable data={visibleRankings} columns={columns} virtualized />
      </div>

      {hasSingleEventBonus && (
        <p className="mt-4 text-sm text-muted-foreground italic">
          * Teams who competed at only one event get Event 2 points based on
          their Event 1 performance. See the{' '}
          <a
            href={`https://firstfrc.blob.core.windows.net/frc${year}/Manual/${year}GameManual.pdf`}
            target="_blank"
            rel="noreferrer"
          >
            {year} Game Manual
          </a>{' '}
          for details.
        </p>
      )}
    </div>
  );
}

function EventPoints({
  points,
  eventNames,
}: {
  points: NonNullable<RegionalRanking['event_points']>[number] | undefined;
  eventNames: Record<string, string>;
}) {
  if (!points) {
    return '-';
  }

  return (
    <Tooltip>
      <TooltipTrigger render={<EventLink eventOrKey={points.event_key} />}>
        {points.total}
      </TooltipTrigger>
      <TooltipContent side="top">
        {eventNames[points.event_key] ?? points.event_key}
      </TooltipContent>
    </Tooltip>
  );
}

function SecondEventPoints({
  ranking,
  eventNames,
}: {
  ranking: RegionalRanking;
  eventNames: Record<string, string>;
}) {
  const points = ranking.event_points?.[1];
  const bonus = ranking.single_event_bonus ?? 0;

  if (points || bonus === 0) {
    return <EventPoints points={points} eventNames={eventNames} />;
  }

  return (
    <Tooltip>
      <TooltipTrigger render={<span className="cursor-help" />}>
        {bonus}*
      </TooltipTrigger>
      <TooltipContent side="top">
        Awarded based on first event performance
      </TooltipContent>
    </Tooltip>
  );
}

function AdvancementBadge({
  advancement,
  eventNames,
}: {
  advancement: RegionalAdvancement | undefined;
  eventNames: Record<string, string>;
}) {
  if (!advancement) {
    return null;
  }

  switch (advancement.cmp_status) {
    case 'PreQualified':
      return (
        <Badge variant="secondary" className="whitespace-nowrap">
          Pre-Qualified
        </Badge>
      );
    case 'EventQualified': {
      const eventKey = advancement.qualifying_event;
      const award = advancement.qualifying_award_name ?? 'Event Qualified';
      if (!eventKey) {
        return <Badge className="whitespace-nowrap">{award}</Badge>;
      }
      return (
        <EventLink eventOrKey={eventKey}>
          <Badge>
            {award} at {eventNames[eventKey] ?? eventKey}
          </Badge>
        </EventLink>
      );
    }
    case 'PoolQualified':
      return (
        <Badge variant="success" className="whitespace-nowrap">
          Regional Pool Week {advancement.qualifying_pool_week}
        </Badge>
      );
    case 'Declined':
      return (
        <Badge variant="destructive" className="whitespace-nowrap">
          Declined
        </Badge>
      );
    default:
      return null;
  }
}
