import { useQuery } from '@tanstack/react-query';
import { ColumnDef } from '@tanstack/react-table';
import { range } from 'lodash-es';
import { useMemo, useState } from 'react';
import { Link, useLoaderData } from 'react-router';

import BiCalendar from '~icons/bi/calendar';
import BiGraphUp from '~icons/bi/graph-up';
import BiInfoCircleFill from '~icons/bi/info-circle-fill';
import BiLink from '~icons/bi/link';
import BiListOl from '~icons/bi/list-ol';
import BiPinMapFill from '~icons/bi/pin-map-fill';
import BiTrophy from '~icons/bi/trophy';
import MdiFolderMediaOutline from '~icons/mdi/folder-media-outline';
import MdiGraphBoxOutline from '~icons/mdi/graph-box-outline';
import MdiRobot from '~icons/mdi/robot';
import MdiTournament from '~icons/mdi/tournament';
import MdiVideo from '~icons/mdi/video';

import { getEventColors } from '~/api/colors';
import {
  Award,
  EventCoprs,
  Match,
  Media,
  Team,
  getEvent,
  getEventAlliances,
  getEventMatches,
} from '~/api/tba/read';
import {
  getEventAwardsOptions,
  getEventCoprsOptions,
  getEventRankingsOptions,
  getEventTeamMediaOptions,
  getEventTeamsOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import AllianceSelectionTable from '~/components/tba/allianceSelectionTable';
import AwardRecipientLink from '~/components/tba/awardRecipientLink';
import CoprScatterChart from '~/components/tba/charts/coprScatterChart';
import { DataTable } from '~/components/tba/dataTable';
import InlineIcon from '~/components/tba/inlineIcon';
import { LocationLink, TeamLink } from '~/components/tba/links';
import {
  CHANGE_IN_COMP_LEVEL_BREAKER,
  CHANGE_IN_DOUBLE_ELIM_ROUND_BREAKER,
  END_OF_DAY_BREAKER,
  START_OF_ELIMS_BREAKER,
  START_OF_QUALS_BREAKER,
} from '~/components/tba/match/breakers';
import SimpleMatchRowsWithBreaks from '~/components/tba/match/matchRows';
import RankingsTable from '~/components/tba/rankingsTable';
import TeamAvatar from '~/components/tba/teamAvatar';
import { Avatar, AvatarImage } from '~/components/ui/avatar';
import { Badge } from '~/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '~/components/ui/dialog';
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
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { SEASON_EVENT_TYPES } from '~/lib/api/EventType';
import { sortAwardsComparator } from '~/lib/awardUtils';
import {
  getCurrentWeekEvents,
  getEventDateString,
  isValidEventKey,
} from '~/lib/eventUtils';
import {
  calculateMedianTurnaroundTime,
  getHighScoreMatch,
  sortMatchComparator,
} from '~/lib/matchUtils';
import { getTeamPreferredRobotPicMedium } from '~/lib/mediaUtils';
import {
  RANKING_POINT_LABELS,
  getBonusRankingPoints,
} from '~/lib/rankingPoints';
import { sortTeamKeysComparator, sortTeamsComparator } from '~/lib/teamUtils';
import {
  STATE_TO_ABBREVIATION,
  camelCaseToHumanReadable,
  cn,
  splitIntoNChunks,
} from '~/lib/utils';

import { Route } from '.react-router/types/app/routes/+types/event.$eventKey';

async function loadData(params: Route.LoaderArgs['params']) {
  if (!isValidEventKey(params.eventKey)) {
    throw new Response(null, {
      status: 404,
    });
  }

  const [event, matches, alliances] = await Promise.all([
    getEvent({ path: { event_key: params.eventKey } }),
    getEventMatches({ path: { event_key: params.eventKey } }),
    getEventAlliances({ path: { event_key: params.eventKey } }),
  ]);

  if (event.data == undefined) {
    throw new Response(null, {
      status: 404,
    });
  }

  if (matches.data == undefined || alliances.data == undefined) {
    throw new Response(null, {
      status: 500,
    });
  }

  return {
    event: event.data,
    matches: matches.data,
    alliances: alliances.data,
    shouldPreviewAwardsTab: SEASON_EVENT_TYPES.has(event.data.event_type),
    shouldPreviewInsightsTab: matches.data.length > 0,
    shouldPreviewRankingsTab: matches.data.length > 0,
  };
}

export async function loader({ params }: Route.LoaderArgs) {
  return await loadData(params);
}

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return await loadData(params);
}

export function meta({ data }: Route.MetaArgs) {
  if (!data) {
    return [
      {
        title: `Event Not Found - The Blue Alliance`,
      },
      {
        name: 'description',
        content: `Videos and match results for the FIRST Robotics Competition.`,
      },
    ];
  }

  return [
    { title: `${data.event.name} (${data.event.year}) - The Blue Alliance` },
    {
      name: 'description',
      content: `Videos and match results for the ${data.event.year} ${data.event.name} FIRST Robotics Competition.`,
    },
  ];
}

export default function EventPage() {
  const {
    event,
    alliances,
    matches,
    shouldPreviewAwardsTab,
    shouldPreviewInsightsTab,
    shouldPreviewRankingsTab,
  } = useLoaderData<Awaited<ReturnType<typeof loadData>>>();

  const awardsQuery = useQuery({
    ...getEventAwardsOptions({ path: { event_key: event.key } }),
  });

  const coprsQuery = useQuery({
    ...getEventCoprsOptions({ path: { event_key: event.key } }),
  });

  const colorsQuery = useQuery({
    queryKey: ['eventColors', event.key],
    queryFn: () => getEventColors({ eventKey: event.key }),
  });

  const rankingsQuery = useQuery({
    ...getEventRankingsOptions({ path: { event_key: event.key } }),
  });

  const teamsQuery = useQuery({
    ...getEventTeamsOptions({ path: { event_key: event.key } }),
  });

  const teamMediaQuery = useQuery({
    ...getEventTeamMediaOptions({ path: { event_key: event.key } }),
  });

  const sortedMatches = useMemo(
    () => matches.sort(sortMatchComparator),
    [matches],
  );

  const quals = useMemo(
    () => sortedMatches.filter((m) => m.comp_level === 'qm'),
    [sortedMatches],
  );

  const elims = useMemo(
    () => sortedMatches.filter((m) => m.comp_level !== 'qm'),
    [sortedMatches],
  );

  const leftSideMatches = (
    <SimpleMatchRowsWithBreaks
      matches={quals.length > 0 ? quals : elims}
      event={event}
      breakers={[
        END_OF_DAY_BREAKER,
        START_OF_QUALS_BREAKER,
        CHANGE_IN_COMP_LEVEL_BREAKER,
      ]}
    />
  );

  const rightSideElims =
    elims.length > 0 ? (
      <SimpleMatchRowsWithBreaks
        matches={elims}
        event={event}
        breakers={[
          END_OF_DAY_BREAKER,
          START_OF_ELIMS_BREAKER,
          CHANGE_IN_COMP_LEVEL_BREAKER,
          CHANGE_IN_DOUBLE_ELIM_ROUND_BREAKER,
        ]}
      />
    ) : null;

  return (
    <div className="py-8">
      <h1 className="mb-3 text-3xl font-medium">
        {event.name} {event.year}
      </h1>

      <InlineIcon>
        <BiCalendar />
        {getEventDateString(event, 'long')}
        {event.week !== null && (
          <Badge className="mx-2 h-[1.5em] align-text-top">
            Week {event.week + 1}
          </Badge>
        )}
      </InlineIcon>

      <InlineIcon>
        <BiPinMapFill />

        {event.gmaps_url ? (
          <Link to={event.gmaps_url}>
            {event.city}, {event.state_prov}, {event.country}
          </Link>
        ) : (
          <>
            {event.city}, {event.state_prov}, {event.country}
          </>
        )}
      </InlineIcon>
      {event.website && (
        <InlineIcon>
          <BiLink />
          <Link to={event.website}>{event.website}</Link>
        </InlineIcon>
      )}

      {event.first_event_code && (
        <InlineIcon>
          <BiInfoCircleFill />
          Details on{' '}
          <Link
            to={`https://frc-events.firstinspires.org/${event.year}/${event.first_event_code}`}
          >
            FRC Events
          </Link>
        </InlineIcon>
      )}

      <InlineIcon>
        <BiGraphUp />
        <Link to={`https://www.statbotics.io/event/${event.key}`}>
          Statbotics
        </Link>
      </InlineIcon>

      {event.webcasts.length > 0 &&
        getCurrentWeekEvents([event]).length > 0 && (
          <InlineIcon>
            <MdiVideo />
            <Link to={`https://www.thebluealliance.com/gameday/${event.key}`}>
              GameDay
            </Link>
          </InlineIcon>
        )}

      <Tabs
        defaultValue={matches.length > 0 ? 'results' : 'teams'}
        className="mt-4"
      >
        <TabsList
          className="flex h-auto flex-wrap items-center justify-evenly
            *:basis-1/2 lg:*:basis-1"
        >
          {(matches.length > 0 || alliances.length > 0) && (
            <TabsTrigger value="results">
              <InlineIcon>
                <MdiTournament />
                Results
              </InlineIcon>
            </TabsTrigger>
          )}
          {(shouldPreviewRankingsTab ||
            (rankingsQuery.data && rankingsQuery.data.rankings.length > 0)) && (
            <TabsTrigger value="rankings">
              <InlineIcon>
                <BiListOl />
                Rankings
              </InlineIcon>
            </TabsTrigger>
          )}
          {((shouldPreviewAwardsTab && awardsQuery.isPending) ||
            (awardsQuery.data !== undefined &&
              awardsQuery.data.length > 0)) && (
            <TabsTrigger value="awards">
              <InlineIcon>
                <BiTrophy />
                Awards
              </InlineIcon>
            </TabsTrigger>
          )}
          <TabsTrigger value="teams">
            <InlineIcon>
              <MdiRobot />
              Teams
              <Badge className="mx-2 h-[1.5em] align-text-top" variant="inline">
                {teamsQuery.data?.length ?? '-'}
              </Badge>
            </InlineIcon>
          </TabsTrigger>
          {((shouldPreviewInsightsTab &&
            (coprsQuery.isPending || colorsQuery.isPending)) ||
            (coprsQuery.data && colorsQuery.data)) &&
            matches.length > 0 && (
              <TabsTrigger value="insights">
                <InlineIcon>
                  <MdiGraphBoxOutline />
                  Insights
                </InlineIcon>
              </TabsTrigger>
            )}
          <TabsTrigger value="media">
            <InlineIcon>
              <MdiFolderMediaOutline />
              Media
            </InlineIcon>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="results">
          <div className="flex flex-wrap gap-4 lg:flex-nowrap">
            <div className="basis-full lg:basis-1/2">{leftSideMatches}</div>

            <div className="basis-full lg:basis-1/2">
              {alliances.length > 0 && (
                <AllianceSelectionTable
                  alliances={alliances}
                  year={event.year}
                />
              )}
              {rightSideElims}
            </div>
          </div>
        </TabsContent>

        {rankingsQuery.data && (
          <TabsContent value="rankings">
            <RankingsTable
              rankings={rankingsQuery.data}
              winners={
                alliances.find((a) => a.status?.status === 'won')?.picks ?? []
              }
            />
          </TabsContent>
        )}

        <TabsContent value="awards">
          {awardsQuery.data && <AwardsTab awards={awardsQuery.data} />}
        </TabsContent>

        <TabsContent value="teams">
          {teamsQuery.data && teamMediaQuery.data && (
            <TeamsTab teams={teamsQuery.data} media={teamMediaQuery.data} />
          )}
        </TabsContent>

        <TabsContent value="insights">
          <MatchStatsTable
            matches={sortedMatches.filter(
              (m) =>
                m.alliances.red.score !== -1 && m.alliances.blue.score !== -1,
            )}
            year={event.year}
          />
          {coprsQuery.data && Object.keys(coprsQuery.data).length > 0 && (
            <>
              <CoprScatterChart
                colors={
                  colorsQuery.data?.status === 200
                    ? colorsQuery.data.data
                    : { teams: {} }
                }
                coprs={coprsQuery.data}
              />
              <ComponentsTable coprs={coprsQuery.data} year={event.year} />
            </>
          )}
        </TabsContent>

        <TabsContent value="media">media</TabsContent>
      </Tabs>
    </div>
  );
}

function AwardsTab({ awards }: { awards: Award[] }) {
  awards.sort(sortAwardsComparator);
  return (
    <div className="flex flex-wrap-reverse">
      <div className="mt-1 flow-root w-full">
        <dl className="divide-y divide-gray-100 text-sm">
          {awards.map((award) => (
            <div
              key={award.name}
              className="grid grid-cols-1 gap-1 py-2 sm:grid-cols-3 sm:gap-4
                sm:px-10"
            >
              <dt className="font-medium text-gray-900 sm:col-span-2">
                {award.name}
              </dt>
              <dd className="text-gray-700 sm:text-right">
                {award.recipient_list
                  .sort((a, b) =>
                    sortTeamKeysComparator(
                      a.team_key ?? '0',
                      b.team_key ?? '0',
                    ),
                  )
                  .map((r, i) => [
                    i > 0 && (r.awardee ? <br /> : ', '),
                    <AwardRecipientLink
                      recipient={r}
                      key={`${award.award_type}-${r.awardee}-${r.team_key}`}
                      year={award.year}
                    />,
                  ])}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}

function TeamsTab({ teams, media }: { teams: Team[]; media: Media[] }) {
  teams.sort(sortTeamsComparator);

  const teamChunks = splitIntoNChunks(teams, 2);

  return (
    <div className="flex flex-row flex-wrap md:flex-nowrap">
      {teamChunks.map((chunk, idx) => (
        <Table key={`chunk-${idx}`}>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[60px] text-center">Avatar</TableHead>
              <TableHead className="w-[30ch]">Team</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Pic</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {chunk.map((t) => {
              const teamMedia = media.filter((m) =>
                m.team_keys.includes(t.key),
              );

              const maybeAvatar = teamMedia.find((m) => m.type === 'avatar');
              const maybeRobotPic = getTeamPreferredRobotPicMedium(teamMedia);

              const abbreviatedStateProv =
                STATE_TO_ABBREVIATION.get(t.state_prov ?? '') ?? t.state_prov;

              const teamLocation = `${t.city}, ${abbreviatedStateProv}, ${t.country}`;

              return (
                <TableRow key={t.key}>
                  <TableCell
                    className={cn({
                      'h-[61px]': maybeAvatar === undefined,
                    })}
                  >
                    {maybeAvatar && (
                      <div
                        className="flex h-full w-full items-center
                          justify-center"
                      >
                        <TeamAvatar media={maybeAvatar} />
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="mt-1 flex flex-col">
                    <TeamLink teamOrKey={t.key}>{t.team_number}</TeamLink>
                    <div>{t.nickname}</div>
                  </TableCell>
                  <TableCell className={'text-xs'}>
                    <LocationLink
                      city={t.city ?? ''}
                      state_prov={t.state_prov ?? ''}
                      country={t.country ?? ''}
                    >
                      {teamLocation}
                    </LocationLink>
                  </TableCell>
                  {maybeRobotPic && (
                    <TableCell>
                      <Dialog>
                        <DialogTrigger className="align-middle">
                          <Avatar className="size-12 cursor-pointer">
                            <AvatarImage src={maybeRobotPic} />
                          </Avatar>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>
                              <TeamLink teamOrKey={t.key}>
                                Team {t.team_number} - {t.nickname}
                              </TeamLink>
                            </DialogTitle>
                            <DialogDescription>
                              <img
                                src={maybeRobotPic}
                                alt=""
                                className="max-h-[80vh] w-3xl rounded-lg
                                  object-cover"
                                loading="lazy"
                              />
                            </DialogDescription>
                          </DialogHeader>
                        </DialogContent>
                      </Dialog>
                    </TableCell>
                  )}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      ))}
    </div>
  );
}

function MatchStatsTable({
  matches,
  year,
}: {
  matches: Match[];
  year: number;
}) {
  const highScoreQual = useMemo(
    () => getHighScoreMatch(matches.filter((m) => m.comp_level === 'qm')),
    [matches],
  );
  const highScorePlayoff = useMemo(
    () => getHighScoreMatch(matches.filter((m) => m.comp_level !== 'qm')),
    [matches],
  );
  const medianTurnaround = useMemo(
    () => calculateMedianTurnaroundTime(matches),
    [matches],
  );

  const rpPercentages = useMemo(
    () =>
      range(0, (RANKING_POINT_LABELS[year] ?? []).length).map(
        (i) =>
          matches
            .filter((m) => m.score_breakdown !== null)
            .map((m) => [
              getBonusRankingPoints(m.score_breakdown?.red ?? {}),
              getBonusRankingPoints(m.score_breakdown?.blue ?? {}),
            ])
            .map((rps) => (rps[0][i] ? 1 : 0) + (rps[1][i] ? 1 : 0))
            .reduce((prev, curr) => prev + curr, 0) /
          Math.max(1, matches.length * 2),
      ),
    [matches, year],
  );

  return (
    <Table>
      <TableBody>
        <TableRow>
          <TableCell>Total Matches</TableCell>
          <TableCell>{matches.length}</TableCell>
        </TableRow>
        {highScoreQual && (
          <TableRow>
            <TableCell>High Score (Quals)</TableCell>
            <TableCell>
              Qual {highScoreQual.match_number} -{' '}
              {Math.max(
                highScoreQual.alliances.red.score,
                highScoreQual.alliances.blue.score,
              )}{' '}
              points
            </TableCell>
          </TableRow>
        )}
        {highScorePlayoff && (
          <TableRow>
            <TableCell>High Score (Playoffs)</TableCell>
            <TableCell>
              {highScorePlayoff.comp_level.toUpperCase()}
              {highScorePlayoff.set_number}-{highScorePlayoff.match_number} -{' '}
              {Math.max(
                highScorePlayoff.alliances.red.score,
                highScorePlayoff.alliances.blue.score,
              )}{' '}
              points
            </TableCell>
          </TableRow>
        )}
        {medianTurnaround !== undefined && (
          <TableRow>
            <TableCell>Median Turnaround Time</TableCell>
            <TableCell>{(medianTurnaround / 60).toFixed(2)} mins</TableCell>
          </TableRow>
        )}
        {rpPercentages.map((rp, i) => (
          <TableRow key={i}>
            <TableCell>{RANKING_POINT_LABELS[year][i]} percentage</TableCell>
            <TableCell>{(rp * 100).toPrecision(2)}%</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function ComponentsTable({ coprs, year }: { coprs: EventCoprs; year: number }) {
  const [component, setComponent] = useState('totalPoints');

  // filter any components that are just all zeros
  const excludedComponents = Object.keys(coprs).filter((k) =>
    Object.values(coprs[k]).every((v) => v === 0),
  );

  const columns: ColumnDef<{ teamKey: string; value: number }>[] = [
    {
      header: 'Team',
      accessorFn: (row) => row.teamKey,
      cell: (cell) => (
        <TeamLink teamOrKey={cell.getValue<string>()} year={year}>
          {cell.getValue<string>().substring(3)}
        </TeamLink>
      ),
    },
    {
      header: 'Value',
      accessorFn: (row) => row.value.toFixed(2),
    },
  ];

  return (
    <div>
      <Card>
        <CardHeader>
          <CardTitle>
            <div className="flex items-center">
              <span className="basis-1/2">Component OPRs</span>
              <Select onValueChange={setComponent}>
                <SelectTrigger className="font-normal">
                  <SelectValue
                    placeholder={camelCaseToHumanReadable(component)}
                  />
                </SelectTrigger>
                <SelectContent>
                  {Object.keys(coprs)
                    .filter((k) => !excludedComponents.includes(k))
                    .map((k) => (
                      <SelectItem key={k} value={k}>
                        {camelCaseToHumanReadable(k)}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          </CardTitle>
          <CardDescription></CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns}
            data={Object.entries(coprs[component])
              .map(([k, v]) => ({
                teamKey: k,
                value: v,
              }))
              .toSorted((a, b) => b.value - a.value)}
          />
        </CardContent>
      </Card>
    </div>
  );
}
