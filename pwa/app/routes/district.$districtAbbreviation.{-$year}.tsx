import { createFileRoute, notFound, useNavigate } from '@tanstack/react-router';
import { groupBy, sumBy } from 'lodash-es';
import { Temporal } from 'temporal-polyfill';

import {
  Award,
  DistrictRanking,
  Event,
  Team,
  getDistrictAwards,
  getDistrictEvents,
  getDistrictHistory,
  getDistrictRankings,
  getDistrictTeams,
} from '~/api/tba/read';
import { TitledCard } from '~/components/tba/cards';
import { DataTable } from '~/components/tba/dataTable';
import {
  EventLink,
  EventLocationLink,
  TeamLink,
  TeamLocationLink,
} from '~/components/tba/links';
import { Badge } from '~/components/ui/badge';
import { Divider } from '~/components/ui/divider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
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
import { AwardType } from '~/lib/api/AwardType';
import { EventType } from '~/lib/api/EventType';
import {
  getCurrentWeekEvents,
  getEventDateString,
  sortEvents,
} from '~/lib/eventUtils';
import { sortTeams } from '~/lib/teamUtils';
import {
  USA_STATE_ABBREVIATION_TO_FULL,
  joinComponents,
  parseParamsForYearElseDefault,
  publicCacheControlHeaders,
} from '~/lib/utils';

export const Route = createFileRoute(
  '/district/$districtAbbreviation/{-$year}',
)({
  loader: async ({ params, context: { queryClient } }) => {
    const year = await parseParamsForYearElseDefault(queryClient, params);
    if (year === undefined) {
      throw notFound();
    }

    const [districtHistory, rankings, teams, events, awards] =
      await Promise.all([
        await getDistrictHistory({
          path: {
            district_abbreviation: params.districtAbbreviation,
          },
        }),
        await getDistrictRankings({
          path: {
            district_key: `${year}${params.districtAbbreviation}`,
          },
        }),
        await getDistrictTeams({
          path: {
            district_key: `${year}${params.districtAbbreviation}`,
          },
        }),
        await getDistrictEvents({
          path: {
            district_key: `${year}${params.districtAbbreviation}`,
          },
        }),
        await getDistrictAwards({
          path: {
            district_key: `${year}${params.districtAbbreviation}`,
          },
        }),
      ]);

    if (
      districtHistory.data === undefined ||
      rankings.data === undefined ||
      teams.data === undefined ||
      events.data === undefined ||
      awards.data === undefined
    ) {
      throw notFound();
    }

    // The api returns a lot of teams that previously played in the district but didn't in the given year
    const actuallyActiveRankings =
      rankings.data === null
        ? null
        : rankings.data.filter(
            (r) => r.point_total > 0 && (r.event_points?.length ?? 0) > 0,
          );

    const today = Temporal.Now.plainDateISO();
    const seasonIsComplete = events.data.every(
      (e) =>
        Temporal.PlainDate.compare(Temporal.PlainDate.from(e.end_date), today) <
        0,
    );

    // If the season is done, show only the teams that were actually active (in the rankings)
    // Otherwise, show all teams (since it may be mid-season and some may not have played yet, thus have no ranking)
    const actuallyActiveTeams =
      actuallyActiveRankings === null || !seasonIsComplete
        ? teams.data
        : teams.data.filter((team) =>
            actuallyActiveRankings.find((r) => r.team_key === team.key),
          );

    return {
      abbreviation: params.districtAbbreviation,
      year,
      districtHistory: districtHistory.data,
      rankings: actuallyActiveRankings,
      teams: actuallyActiveTeams,
      events: events.data,
      awards: awards.data,
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
    awards,
    districtHistory,
    events,
    rankings,
    teams,
    year,
  } = Route.useLoaderData();
  const navigate = useNavigate();

  const hasRankings = rankings !== null;

  const validYears = districtHistory.map((d) => d.year).sort((a, b) => b - a);

  const dcmpEvents = events.filter(
    (event) =>
      event.event_type === EventType.DISTRICT_CMP ||
      event.event_type === EventType.DISTRICT_CMP_DIVISION,
  );

  const parentDCMPEvent = dcmpEvents.find(
    (event) => event.event_type === EventType.DISTRICT_CMP,
  );

  const dcmpAwards = awards.filter(
    (award) =>
      dcmpEvents.find((event) => event.key === award.event_key) !== undefined,
  );

  const parentDCMPAwards = dcmpAwards.filter(
    (award) => award.event_key === parentDCMPEvent?.key,
  );

  const thisWeekEvents = getCurrentWeekEvents(events);

  const dcmpChairmanRecipients = dcmpAwards
    .filter((award) => award.award_type === AwardType.CHAIRMANS)
    .flatMap((award) => award.recipient_list)
    .map((recipient) => recipient.team_key)
    .filter((k): k is string => k !== null && k !== undefined);

  const dcmpWinnerRecipients = parentDCMPAwards
    .filter((award) => award.award_type === AwardType.WINNER)
    .flatMap((award) => award.recipient_list)
    .map((recipient) => recipient.team_key)
    .filter((k): k is string => k !== null && k !== undefined);

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
        <Select
          value={String(year)}
          onValueChange={(value) => {
            void navigate({
              to: '/district/$districtAbbreviation/{-$year}',
              params: {
                districtAbbreviation: abbreviation,
                year: value,
              },
            });
          }}
        >
          <SelectTrigger className="w-30">
            <SelectValue placeholder={year} />
          </SelectTrigger>
          <SelectContent className="max-h-[30vh] overflow-y-auto">
            <SelectItem value="stats">Stats</SelectItem>
            {validYears.map((y) => (
              <SelectItem key={y} value={`${y}`}>
                {y}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue={'overview'} className="mt-4">
        <TabsList className="flex h-auto flex-wrap items-center justify-evenly *:basis-1/2 lg:*:basis-1">
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

          {parentDCMPEvent &&
            (dcmpChairmanRecipients.length > 0 ||
              dcmpWinnerRecipients.length > 0) && (
              <>
                <Divider className="py-4">
                  <div className="text-xl">
                    <EventLink eventOrKey={parentDCMPEvent.key}>DCMP</EventLink>
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
                      cardSubtitle={
                        <>
                          {dcmpAwards
                            .find(
                              (award) =>
                                award.award_type === AwardType.CHAIRMANS,
                            )
                            ?.name.replace('Regional', 'District Championship')}
                        </>
                      }
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
                      cardSubtitle={
                        <>
                          {dcmpAwards
                            .find(
                              (award) => award.award_type === AwardType.WINNER,
                            )
                            ?.name.replace('Regional', 'District Championship')}
                        </>
                      }
                    />
                  )}
                </div>
              </>
            )}

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
                    <TeamLink teamOrKey={`frc${cell.getValue()}`} year={year}>
                      {cell.getValue()}
                    </TeamLink>
                  ),
                  accessorFn: (ranking) =>
                    Number(ranking.team_key.substring(3)),
                },
                {
                  header: 'Event 1',
                  cell: (info) => <div>{info.getValue() || '-'}</div>,
                  accessorFn: (ranking) =>
                    getNthNonDcmpEvent(ranking.event_points ?? [], 0)?.total ??
                    0,
                },
                {
                  header: 'Event 2',
                  cell: (info) => <div>{info.getValue() || '-'}</div>,
                  accessorFn: (ranking) =>
                    getNthNonDcmpEvent(ranking.event_points ?? [], 1)?.total ??
                    0,
                },
                {
                  header: 'DCMP',
                  cell: (info) => <div>{info.getValue() || '-'}</div>,
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
                  cell: (info) => <div>{info.getValue() || '-'}</div>,
                  accessorFn: (ranking) => ranking.rookie_bonus ?? 0,
                },
                {
                  header: 'Total',
                  accessorFn: (ranking) => ranking.point_total,
                  cell: (info) => <div>{info.getValue()}</div>,
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
