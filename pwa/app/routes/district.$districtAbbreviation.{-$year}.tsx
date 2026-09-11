import { createFileRoute, notFound } from '@tanstack/react-router';
import { cn } from 'cn';
import { sumBy } from 'lodash-es';
import { Temporal } from 'temporal-polyfill';

import TeamsIcon from '~icons/lucide/bot';
import EventsIcon from '~icons/lucide/calendar-days';
import RankingsIcon from '~icons/lucide/list-ordered';
import ChampsIcon from '~icons/lucide/trophy';

import {
  Award,
  AwardType,
  CmpQualificationMethod,
  DistrictRanking,
  Event,
  EventType,
  Team,
} from '~/api/tba/read';
import {
  getDistrictAdvancementOptions,
  getDistrictAwardsOptions,
  getDistrictEventsOptions,
  getDistrictHistoryOptions,
  getDistrictRankingsOptions,
  getDistrictTeamsOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { DataTable } from '~/components/tba/dataTable';
import { DistrictChampsTab } from '~/components/tba/districtChampsTab';
import InlineIcon from '~/components/tba/inlineIcon';
import {
  EventLink,
  EventLocationLink,
  TeamLink,
  TeamLocationLink,
} from '~/components/tba/links';
import { YearSelector } from '~/components/tba/yearSelector';
import {
  AnimatedTabs,
  AnimatedTabsTrigger,
} from '~/components/ui/animated-tabs';
import { Badge } from '~/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { TabsContent, TabsList } from '~/components/ui/tabs';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import { CMP_QUALIFICATION_METHOD_LABELS } from '~/lib/api/CmpQualificationMethod';
import { getDistrictColorBorderClass } from '~/lib/districtUtils';
import { getEventDateString, sortEvents } from '~/lib/eventUtils';
import { staleTimeForYear } from '~/lib/queryClient';
import { sortTeams } from '~/lib/teamUtils';
import {
  doThrowNotFound,
  joinComponents,
  parseParamsForYearElseDefault,
  publicCacheControlHeaders,
} from '~/lib/utils';

export const Route = createFileRoute(
  '/district/$districtAbbreviation/{-$year}',
)({
  loader: async ({ params, context: { queryClient, currentSeason } }) => {
    const year = parseParamsForYearElseDefault(currentSeason, params);
    if (year === undefined) {
      throw notFound();
    }

    const districtKey = `${year}${params.districtAbbreviation}`;
    const yearStaleTime = staleTimeForYear(year);

    const [districtHistory, rankings, teams, events, awards, advancement] =
      await Promise.all([
        queryClient
          .ensureQueryData({
            ...getDistrictHistoryOptions({
              path: { district_abbreviation: params.districtAbbreviation },
            }),
            staleTime: yearStaleTime,
          })
          .catch(doThrowNotFound),
        queryClient
          .ensureQueryData({
            ...getDistrictRankingsOptions({
              path: { district_key: districtKey },
            }),
            staleTime: yearStaleTime,
          })
          .catch(() => null),
        queryClient
          .ensureQueryData({
            ...getDistrictTeamsOptions({ path: { district_key: districtKey } }),
            staleTime: yearStaleTime,
          })
          .catch(() => []),
        queryClient
          .ensureQueryData({
            ...getDistrictEventsOptions({
              path: { district_key: districtKey },
            }),
            staleTime: yearStaleTime,
          })
          .catch(() => []),
        queryClient
          .ensureQueryData({
            ...getDistrictAwardsOptions({
              path: { district_key: districtKey },
            }),
            staleTime: yearStaleTime,
          })
          .catch(() => []),
        queryClient
          .ensureQueryData({
            ...getDistrictAdvancementOptions({
              path: { district_key: districtKey },
            }),
            staleTime: yearStaleTime,
          })
          .catch(() => null),
      ]);

    if (districtHistory.length === 0) {
      throw notFound();
    }

    // The api returns a lot of teams that previously played in the district but didn't in the given year
    const actuallyActiveRankings =
      rankings === null
        ? null
        : rankings.filter(
            (r) => r.point_total > 0 && (r.event_points?.length ?? 0) > 0,
          );

    const today = Temporal.Now.plainDateISO();
    const seasonIsComplete = events.every(
      (e) =>
        Temporal.PlainDate.compare(Temporal.PlainDate.from(e.end_date), today) <
        0,
    );

    // If the season is done, show only the teams that were actually active (in the rankings)
    // Otherwise, show all teams (since it may be mid-season and some may not have played yet, thus have no ranking)
    const actuallyActiveTeams =
      actuallyActiveRankings === null || !seasonIsComplete
        ? teams
        : teams.filter((team) =>
            actuallyActiveRankings.find((r) => r.team_key === team.key),
          );

    return {
      abbreviation: params.districtAbbreviation,
      currentSeason,
      year,
      districtHistory,
      rankings: actuallyActiveRankings,
      teams: actuallyActiveTeams,
      events,
      awards,
      advancementCutoffs: advancement?.cutoffs ?? null,
    };
  },
  headers: publicCacheControlHeaders(),
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [
          { title: 'The Blue Alliance' },
          {
            name: 'description',
            content: 'District information for the FIRST Robotics Competition.',
          },
        ],
      };
    }

    return {
      meta: [
        {
          title: `${loaderData.year} ${loaderData.districtHistory[loaderData.districtHistory.length - 1].display_name} District - The Blue Alliance`,
        },
        {
          name: 'description',
          content: `District information for the ${loaderData.year} ${loaderData.districtHistory[loaderData.districtHistory.length - 1].display_name} District.`,
        },
      ],
    };
  },
  component: DistrictPage,
});

function DistrictPage() {
  const {
    abbreviation,
    advancementCutoffs,
    awards,
    currentSeason,
    districtHistory,
    events,
    rankings,
    teams,
    year,
  } = Route.useLoaderData();

  const hasRankings = rankings !== null;

  const cmpQualification = advancementCutoffs?.cmp_qualification ?? {};
  const cmpDeclines = new Set(advancementCutoffs?.cmp_declines ?? []);
  const dcmpDeclines = new Set(advancementCutoffs?.dcmp_declines ?? []);

  const validYears = districtHistory.map((d) => d.year).sort((a, b) => b - a);

  const parentDCMPEvents = sortEvents(
    events.filter((event) => event.event_type === EventType.DISTRICT_CMP),
  );
  const eventCount = events.filter(
    (event) => event.event_type !== EventType.DISTRICT_CMP_DIVISION,
  );
  const districtColor = getDistrictColorBorderClass(abbreviation);

  return (
    <div className="py-8">
      <div
        className="flex flex-col gap-4 sm:flex-row sm:items-start
          sm:justify-between"
      >
        <div className={cn(districtColor && 'border-l-4 pl-4', districtColor)}>
          <h1 className="text-3xl font-medium">
            {districtHistory[districtHistory.length - 1].display_name} {year}
          </h1>
          <div
            className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm
              text-muted-foreground"
          >
            <span>{teams.length} teams</span>
            <span aria-hidden="true">&middot;</span>
            <span>{eventCount.length} events</span>
            {parentDCMPEvents.map((event) => (
              <span key={event.key} className="contents">
                <span aria-hidden="true">&middot;</span>
                <EventLink eventOrKey={event.key}>
                  {parentDCMPEvents.length === 1
                    ? 'District Championship'
                    : event.short_name || event.name}
                </EventLink>
              </span>
            ))}
          </div>
        </div>
        <YearSelector
          currentLabel={String(year)}
          triggerClassName="w-full sm:w-30"
          options={[
            {
              label: 'Insights',
              to: `/district/${abbreviation}/insights`,
            },
            ...validYears.map((y) => ({
              label: String(y),
              to: `/district/${abbreviation}/${y}`,
              isCurrent: y === year,
            })),
          ]}
        />
      </div>

      <AnimatedTabs
        defaultValue={hasRankings ? 'rankings' : 'events'}
        className="mt-6"
      >
        <TabsList
          className="flex h-auto flex-wrap items-center justify-evenly
            *:basis-1/2 lg:*:basis-1"
        >
          {hasRankings && (
            <AnimatedTabsTrigger value="rankings">
              <InlineIcon>
                <RankingsIcon />
                Rankings
              </InlineIcon>
            </AnimatedTabsTrigger>
          )}
          <AnimatedTabsTrigger value="events">
            <InlineIcon>
              <EventsIcon />
              Events
            </InlineIcon>
          </AnimatedTabsTrigger>
          <AnimatedTabsTrigger value="teams">
            <InlineIcon>
              <TeamsIcon />
              Teams
            </InlineIcon>
          </AnimatedTabsTrigger>
          <AnimatedTabsTrigger value="champs">
            <InlineIcon>
              <ChampsIcon />
              Champs
            </InlineIcon>
          </AnimatedTabsTrigger>
        </TabsList>

        {hasRankings && (
          <TabsContent value="rankings" className="pt-2">
            <DataTable
              data={rankings}
              columns={[
                { header: 'Rank', accessorFn: (ranking) => ranking.rank },
                {
                  header: 'Team',
                  cell: (cell) => (
                    <TeamLink
                      teamOrKey={`frc${cell.getValue<number>()}`}
                      year={year}
                    >
                      {cell.getValue<number>()}
                    </TeamLink>
                  ),
                  accessorFn: (ranking) =>
                    Number(ranking.team_key.substring(3)),
                },
                {
                  header: 'Event 1',
                  cell: (info) => <div>{info.getValue<number>() || '-'}</div>,
                  accessorFn: (ranking) =>
                    getNthNonDcmpEvent(ranking.event_points ?? [], 0)?.total ??
                    0,
                },
                {
                  header: 'Event 2',
                  cell: (info) => <div>{info.getValue<number>() || '-'}</div>,
                  accessorFn: (ranking) =>
                    getNthNonDcmpEvent(ranking.event_points ?? [], 1)?.total ??
                    0,
                },
                {
                  header: 'Pre-DCMP',
                  cell: (info) => <div>{info.getValue<number>() || '-'}</div>,
                  accessorFn: (ranking) =>
                    sumBy(
                      ranking.event_points?.filter(
                        (event) => !event.district_cmp,
                      ),
                      (r) => r.total,
                    ),
                },
                {
                  header: 'DCMP',
                  cell: (info) => <div>{info.getValue<number>() || '-'}</div>,
                  accessorFn: (ranking) =>
                    sumBy(
                      ranking.event_points?.filter(
                        (event) => event.district_cmp,
                      ),
                      (r) => r.total,
                    ),
                },
                {
                  header: 'Age Bonus',
                  cell: (info) => <div>{info.getValue<number>() || '-'}</div>,
                  accessorFn: (ranking) => ranking.rookie_bonus ?? 0,
                },
                {
                  header: 'Total',
                  accessorFn: (ranking) => ranking.point_total,
                  cell: (info) => <div>{info.getValue<number>()}</div>,
                },
                {
                  header: 'Advancement',
                  accessorFn: (ranking) =>
                    cmpQualification[ranking.team_key] ?? null,
                  cell: (info) => {
                    const { team_key, event_points } = info.row.original;

                    if (cmpDeclines.has(team_key)) {
                      return <Badge variant="destructive">Declined CMP</Badge>;
                    }

                    const method =
                      info.getValue<CmpQualificationMethod | null>();
                    if (method) {
                      return (
                        <Badge variant="success" className="whitespace-nowrap">
                          {CMP_QUALIFICATION_METHOD_LABELS[method]}
                        </Badge>
                      );
                    }

                    if (dcmpDeclines.has(team_key)) {
                      return <Badge variant="destructive">Declined DCMP</Badge>;
                    }

                    const dcmpPoints = sumBy(
                      event_points?.filter((event) => event.district_cmp),
                      (event) => event.total,
                    );
                    return dcmpPoints > 0 ? (
                      <Badge variant="secondary">DCMP</Badge>
                    ) : null;
                  },
                },
              ]}
            />
          </TabsContent>
        )}
        <TabsContent value="events" className="pt-2">
          <DistrictEventsTable awards={awards} events={events} />
        </TabsContent>
        <TabsContent value="teams" className="pt-2">
          <DistrictTeamsTable teams={teams} year={year} />
        </TabsContent>
        <TabsContent value="champs" className="pt-2">
          <DistrictChampsTab
            abbreviation={abbreviation}
            currentSeason={currentSeason}
            year={year}
          />
        </TabsContent>
      </AnimatedTabs>
    </div>
  );
}

function DistrictEventsTable({
  awards,
  events,
}: {
  awards: Award[];
  events: Event[];
}) {
  const sortedEvents = sortEvents(events);

  return (
    <Table className="table-fixed">
      <TableHeader>
        <TableRow>
          <TableHead className="w-2/5 px-2 sm:w-1/4 sm:px-4">Event</TableHead>
          <TableHead className="w-[15%] px-1 text-center sm:w-1/4 sm:px-4">
            <span className="sm:hidden">Wk</span>
            <span className="hidden sm:inline">Dates</span>
          </TableHead>
          <TableHead className="w-[22.5%] px-1 sm:w-1/4 sm:px-4">
            Winners
          </TableHead>
          <TableHead className="w-[22.5%] px-1 sm:w-1/4 sm:px-4">
            Impact
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortedEvents.map((event, index) => {
          const isDistrictChampionship =
            event.event_type === EventType.DISTRICT_CMP ||
            event.event_type === EventType.DISTRICT_CMP_DIVISION;
          const startsNewWeek =
            index > 0 && event.week !== sortedEvents[index - 1]?.week;

          return (
            <TableRow
              key={event.key}
              className={cn(
                isDistrictChampionship && 'bg-primary/5 hover:bg-primary/10',
                startsNewWeek &&
                  'border-t-2 border-t-border dark:border-t-muted-foreground/70',
              )}
            >
              <TableCell className="px-2 align-top sm:px-4">
                <div className="flex flex-wrap items-center gap-2">
                  <EventLink
                    eventOrKey={event.key}
                    className="text-foreground hover:underline"
                  >
                    {event.short_name}
                  </EventLink>
                </div>
                <div
                  className="mt-0.5 text-xs text-muted-foreground
                    [&_a]:text-muted-foreground [&_a:hover]:text-foreground"
                >
                  <EventLocationLink event={event} hideUSA hideVenue />
                </div>
              </TableCell>
              <TableCell className="px-1 text-center align-top sm:px-4">
                {event.week !== null && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger
                        render={
                          <Badge
                            variant="secondary"
                            className="cursor-help whitespace-nowrap"
                          />
                        }
                      >
                        <span className="sm:hidden">Wk {event.week + 1}</span>
                        <span className="hidden sm:inline">
                          Week {event.week + 1}
                        </span>
                      </TooltipTrigger>
                      <TooltipContent side="top">
                        {getEventDateString(event, 'short')}
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </TableCell>
              <TableCell className="px-1 align-top sm:px-4">
                {joinComponents(
                  awards
                    .filter(
                      (a) =>
                        a.event_key === event.key &&
                        a.award_type === AwardType.WINNER,
                    )
                    .flatMap((a) => a.recipient_list)
                    .map((r) => r.team_key)
                    .filter((k) => k !== null)
                    .map((k) => (
                      <TeamLink teamOrKey={k} year={event.year} key={k}>
                        {k.substring(3)}
                      </TeamLink>
                    )),
                  ', ',
                )}
              </TableCell>
              <TableCell className="px-1 align-top sm:px-4">
                {joinComponents(
                  awards
                    .filter(
                      (a) =>
                        a.event_key === event.key &&
                        a.award_type === AwardType.CHAIRMANS,
                    )
                    .flatMap((a) => a.recipient_list)
                    .map((r) => r.team_key)
                    .filter((k) => k !== null)
                    .map((k) => (
                      <TeamLink teamOrKey={k} year={event.year} key={k}>
                        {k.substring(3)}
                      </TeamLink>
                    )),
                  ', ',
                )}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
      <TableFooter>
        <TableRow>
          <TableCell colSpan={3}>Total</TableCell>
          <TableCell className="text-right">{events.length} Events</TableCell>
        </TableRow>
      </TableFooter>
    </Table>
  );
}

function DistrictTeamsTable({ teams, year }: { teams: Team[]; year: number }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="">Team</TableHead>
          <TableHead>Location</TableHead>
          <TableHead>Rookie Year</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortTeams(teams).map((team) => (
          <TableRow key={team.key}>
            <TableCell>
              <TeamLink teamOrKey={team} year={year}>
                {team.team_number} - {team.nickname}
              </TeamLink>
            </TableCell>
            <TableCell>
              <TeamLocationLink team={team} hideUSA />
            </TableCell>
            <TableCell>{team.rookie_year}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function getNthNonDcmpEvent(
  rankings: NonNullable<DistrictRanking['event_points']>,
  n: number,
): NonNullable<DistrictRanking['event_points']>[number] | undefined {
  const events = rankings.filter((event) => !event.district_cmp);

  return events.length <= n ? undefined : events[n];
}
