import { Link, createFileRoute, notFound } from '@tanstack/react-router';
import { groupBy, sumBy } from 'lodash-es';
import { Temporal } from 'temporal-polyfill';

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
import { TitledCard } from '~/components/tba/cards';
import { DataTable } from '~/components/tba/dataTable';
import {
  EventLink,
  EventLocationLink,
  TeamLink,
  TeamLocationLink,
} from '~/components/tba/links';
import { YearSelector } from '~/components/tba/yearSelector';
import { Badge } from '~/components/ui/badge';
import { Divider } from '~/components/ui/divider';
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { CMP_QUALIFICATION_METHOD_LABELS } from '~/lib/api/CmpQualificationMethod';
import {
  getCurrentWeekEvents,
  getEventDateString,
  sortEvents,
} from '~/lib/eventUtils';
import { staleTimeForYear } from '~/lib/queryClient';
import { sortTeams } from '~/lib/teamUtils';
import {
  USA_STATE_ABBREVIATION_TO_FULL,
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

  const dcmpEvents = events.filter(
    (event) =>
      event.event_type === EventType.DISTRICT_CMP ||
      event.event_type === EventType.DISTRICT_CMP_DIVISION,
  );

  const parentDCMPEvents = sortEvents(
    dcmpEvents.filter((event) => event.event_type === EventType.DISTRICT_CMP),
  );

  const thisWeekEvents = getCurrentWeekEvents(events);

  const teamsByLocation = groupBy(teams, (team) =>
    team.country === 'USA' ? team.state_prov : team.country,
  );
  const eventsByLocation = groupBy(
    events.filter((e) => e.event_type !== EventType.DISTRICT_CMP_DIVISION),
    (event) =>
      event.country === 'USA'
        ? USA_STATE_ABBREVIATION_TO_FULL.get(event.state_prov ?? '')
        : event.country,
  );

  return (
    <div>
      <div className="mt-4 flex items-center justify-between gap-4">
        <h1 className="text-4xl font-medium">
          {districtHistory[districtHistory.length - 1].display_name} {year}
        </h1>
        <Link
          to="/district/$districtAbbreviation/champs/$year"
          params={{ districtAbbreviation: abbreviation, year: String(year) }}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          Follow teams at FIRST Championship
        </Link>
        <YearSelector
          currentLabel={String(year)}
          triggerClassName="w-30"
          options={[
            {
              label: 'Stats',
              to: `/district/${abbreviation}/stats`,
            },
            ...validYears.map((y) => ({
              label: String(y),
              to: `/district/${abbreviation}/${y}`,
              isCurrent: y === year,
            })),
          ]}
        />
      </div>

      <Tabs defaultValue={'overview'} className="mt-4">
        <TabsList
          className="flex h-auto flex-wrap items-center justify-evenly
            *:basis-1/2 lg:*:basis-1"
        >
          <TabsTrigger value="overview">Overview</TabsTrigger>
          {hasRankings && <TabsTrigger value="rankings">Rankings</TabsTrigger>}
          <TabsTrigger value="events">Events</TabsTrigger>
          <TabsTrigger value="teams">Teams</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="gap-3 lg:grid lg:grid-cols-2">
            <TitledCard cardTitle={teams.length} cardSubtitle={'Teams'} />
            <TitledCard
              cardTitle={
                events.filter(
                  (e) => e.event_type !== EventType.DISTRICT_CMP_DIVISION,
                ).length
              }
              cardSubtitle={'Events'}
            />
          </div>

          {Object.keys(teamsByLocation).length > 1 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="">State</TableHead>
                  <TableHead>Teams</TableHead>
                  <TableHead>Events</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(teamsByLocation)
                  .sort((a, b) => b[1].length - a[1].length)
                  .map(([location, locationTeams]) => {
                    const locationEvents = eventsByLocation[location] ?? [];

                    return (
                      <TableRow key={location}>
                        <TableCell>{location}</TableCell>
                        <TableCell className="pl-4">
                          {locationTeams.length}
                        </TableCell>
                        <TableCell className="pl-4">
                          {locationEvents.length}
                          {locationEvents.find(
                            (e) => e.event_type === EventType.DISTRICT_CMP,
                          ) ? (
                            <Badge className="ml-2">DCMP</Badge>
                          ) : (
                            ''
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
              </TableBody>
            </Table>
          )}

          {thisWeekEvents.length > 0 && (
            <>
              <Divider className="py-4">
                <div className="text-xl">This Week</div>
              </Divider>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Event</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Dates</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {thisWeekEvents.map((event) => (
                    <TableRow key={event.key}>
                      <TableCell>
                        <EventLink eventOrKey={event.key}>
                          {event.name}
                        </EventLink>
                      </TableCell>
                      <TableCell>
                        <EventLocationLink event={event} hideUSA hideVenue />
                      </TableCell>
                      <TableCell>
                        {getEventDateString(event, 'short')}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </>
          )}

          {parentDCMPEvents.map((parentDCMPEvent) => (
            <DistrictDCMPOverviewSection
              key={parentDCMPEvent.key}
              parentDCMPEvent={parentDCMPEvent}
              showDetailedName={parentDCMPEvents.length > 1}
              awards={awards}
              year={year}
            />
          ))}

          {hasRankings && rankings !== null && rankings.length > 0 && (
            <>
              <Divider className="py-4">
                <div className="text-xl">Top Teams</div>
              </Divider>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Rank</TableHead>
                    <TableHead>Team</TableHead>
                    <TableHead>Points</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[...rankings]
                    .sort((a, b) => (a.rank ?? 0) - (b.rank ?? 0))
                    .slice(0, 25)
                    .map((ranking) => (
                      <TableRow key={ranking.team_key}>
                        <TableCell>{ranking.rank}</TableCell>
                        <TableCell>
                          <TeamLink teamOrKey={ranking.team_key} year={year}>
                            {ranking.team_key.substring(3)}
                          </TeamLink>
                        </TableCell>
                        <TableCell>{ranking.point_total}</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </>
          )}
        </TabsContent>

        {hasRankings && (
          <TabsContent value="rankings">
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
        <TabsContent value="events">
          <DistrictEventsTable awards={awards} events={events} />
        </TabsContent>
        <TabsContent value="teams">
          <DistrictTeamsTable teams={teams} year={year} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function DistrictDCMPOverviewSection({
  parentDCMPEvent,
  showDetailedName,
  awards,
  year,
}: {
  parentDCMPEvent: Event;
  showDetailedName: boolean;
  awards: Award[];
  year: number;
}) {
  const associatedEventKeys = [
    parentDCMPEvent.key,
    ...(parentDCMPEvent.division_keys || []),
  ];

  const parentDCMPAwards = awards.filter((award) =>
    associatedEventKeys.includes(award.event_key),
  );

  const dcmpChairmanRecipients = parentDCMPAwards
    .filter((award) => award.award_type === AwardType.CHAIRMANS)
    .flatMap((award) => award.recipient_list)
    .map((recipient) => recipient.team_key)
    .filter((k): k is string => k !== null && k !== undefined);

  const dcmpWinnerRecipients = parentDCMPAwards
    .filter(
      (award) =>
        award.award_type === AwardType.WINNER &&
        award.event_key === parentDCMPEvent.key,
    )
    .flatMap((award) => award.recipient_list)
    .map((recipient) => recipient.team_key)
    .filter((k): k is string => k !== null && k !== undefined);

  if (
    dcmpChairmanRecipients.length === 0 &&
    dcmpWinnerRecipients.length === 0
  ) {
    return null;
  }

  const chairmanAwardName =
    parentDCMPAwards
      .find((award) => award.award_type === AwardType.CHAIRMANS)
      ?.name.replace('Regional', 'District Championship') ??
    'District Championship FIRST Impact Award';

  const winnerAwardName =
    parentDCMPAwards
      .find(
        (award) =>
          award.award_type === AwardType.WINNER &&
          award.event_key === parentDCMPEvent.key,
      )
      ?.name.replace('Regional', 'District Championship') ??
    'District Championship Winner';

  return (
    <div>
      <Divider className="py-4">
        <div className="text-xl">
          <EventLink eventOrKey={parentDCMPEvent.key}>
            {showDetailedName
              ? parentDCMPEvent.short_name || parentDCMPEvent.name
              : 'DCMP'}
          </EventLink>
        </div>
      </Divider>

      <div className="gap-3 lg:grid lg:grid-cols-2">
        {dcmpChairmanRecipients.length > 0 && (
          <TitledCard
            cardTitle={joinComponents(
              dcmpChairmanRecipients
                .map((k) => k.substring(3))
                .sort((a, b) => Number(a) - Number(b))
                .map((teamNumber) => (
                  <TeamLink
                    teamOrKey={`frc${teamNumber}`}
                    year={year}
                    key={teamNumber}
                  >
                    {teamNumber}
                  </TeamLink>
                )),
              <span className="font-medium">, </span>,
            )}
            cardSubtitle={<>{chairmanAwardName}</>}
          />
        )}
        {dcmpWinnerRecipients.length > 0 && (
          <TitledCard
            cardTitle={joinComponents(
              dcmpWinnerRecipients
                .map((k) => k.substring(3))
                .sort((a, b) => Number(a) - Number(b))
                .map((teamNumber) => (
                  <TeamLink
                    teamOrKey={`frc${teamNumber}`}
                    year={year}
                    key={teamNumber}
                  >
                    {teamNumber}
                  </TeamLink>
                )),
              <span className="font-medium">, </span>,
            )}
            cardSubtitle={<>{winnerAwardName}</>}
          />
        )}
      </div>
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
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="">Event</TableHead>
          <TableHead>Location</TableHead>
          <TableHead>Dates</TableHead>
          <TableHead className="">Winners</TableHead>
          <TableHead className="">Impact</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortEvents(events).map((event) => (
          <TableRow key={event.key}>
            <TableCell>
              <EventLink eventOrKey={event.key}>{event.name}</EventLink>
            </TableCell>
            <TableCell>
              <EventLocationLink event={event} hideUSA hideVenue />
            </TableCell>
            <TableCell>
              {event.week !== null && (
                <Badge variant={'secondary'} className="mr-2">
                  Week {event.week + 1}
                </Badge>
              )}
              {getEventDateString(event, 'short')}
            </TableCell>
            <TableCell>
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
            <TableCell>
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
        ))}
      </TableBody>
      <TableFooter>
        <TableRow>
          <TableCell colSpan={4}>Total</TableCell>
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
