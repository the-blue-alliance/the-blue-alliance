import * as Sentry from '@sentry/tanstackstart-react';
import { useQueries, useSuspenseQuery } from '@tanstack/react-query';
import {
  createFileRoute,
  notFound,
  redirect,
  useNavigate,
} from '@tanstack/react-router';
import { useMemo, useState } from 'react';

import { Award, Event, Match, Team, WltRecord } from '~/api/tba/read';
import {
  getEventAlliancesOptions,
  getEventDistrictPointsOptions,
  getTeamAwardsByYearOptions,
  getTeamEventsByYearOptions,
  getTeamEventsStatusesByYearOptions,
  getTeamMatchesByYearOptions,
  getTeamMediaByYearOptions,
  getTeamOptions,
  getTeamSocialMediaOptions,
  getTeamYearsParticipatedOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { AwardBanner } from '~/components/tba/banner';
import FavoriteButton from '~/components/tba/favoriteButton';
import {
  TableOfContents,
  TableOfContentsSection,
} from '~/components/tba/tableOfContents';
import TeamEventAppearance from '~/components/tba/teamEventAppearance';
import TeamPageTeamInfo from '~/components/tba/teamPageTeamInfo';
import TeamRobotPicsCarousel from '~/components/tba/teamRobotPicsCarousel';
import { Badge } from '~/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import { Separator } from '~/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import { BLUE_BANNER_AWARDS } from '~/lib/api/AwardType';
import { SEASON_EVENT_TYPES } from '~/lib/api/EventType';
import { sortAwardsByEventDate } from '~/lib/awardUtils';
import { sortEventsComparator } from '~/lib/eventUtils';
import {
  calculateTeamRecordsFromMatches,
  getTeamsUnpenalizedHighScore,
} from '~/lib/matchUtils';
import {
  MODEL_TYPE,
  addRecords,
  doThrowNotFound,
  parseParamsForYearElseDefault,
  pluralize,
  publicCacheControlHeaders,
  stringifyRecord,
  winrateFromRecord,
} from '~/lib/utils';

export const Route = createFileRoute('/team/$teamNumber/{-$year}')({
  loader: async ({ params, context: { queryClient } }) => {
    const startTime = Date.now();
    const teamKey = `frc${params.teamNumber}`;
    const year = await parseParamsForYearElseDefault(queryClient, params);

    Sentry.metrics.count('team.page.view', 1, {
      attributes: { team_number: params.teamNumber, year },
    });

    if (year === undefined) {
      throw notFound();
    }

    // spawn these now, we don't need to await them yet though
    const teamMediaQuery = queryClient
      .ensureQueryData(
        getTeamMediaByYearOptions({ path: { team_key: teamKey, year } }),
      )
      .catch(() => []);
    const teamSocialsQuery = queryClient
      .ensureQueryData(
        getTeamSocialMediaOptions({ path: { team_key: teamKey } }),
      )
      .catch(() => ({}));
    const teamMatchesQuery = queryClient
      .ensureQueryData(
        getTeamMatchesByYearOptions({ path: { team_key: teamKey, year } }),
      )
      .catch(() => []);
    const teamStatusesQuery = queryClient
      .ensureQueryData(
        getTeamEventsStatusesByYearOptions({
          path: { team_key: teamKey, year },
        }),
      )
      .catch(() => ({}));
    const teamAwardsQuery = queryClient
      .ensureQueryData(
        getTeamAwardsByYearOptions({ path: { team_key: teamKey, year } }),
      )
      .catch(() => []);
    const teamEventsQuery = queryClient
      .ensureQueryData(
        getTeamEventsByYearOptions({ path: { team_key: teamKey, year } }),
      )
      .catch(() => []);

    // these need to be awaited so we can validate the year
    const [team, yearsParticipated] = await Promise.all([
      queryClient
        .ensureQueryData(getTeamOptions({ path: { team_key: teamKey } }))
        .catch(doThrowNotFound),
      queryClient
        .ensureQueryData(
          getTeamYearsParticipatedOptions({ path: { team_key: teamKey } }),
        )
        .catch((): number[] => []),
    ]);

    if (!yearsParticipated.includes(year)) {
      if (params.year === undefined) {
        throw redirect({
          to: '/team/$teamNumber/history',
          params: { teamNumber: params.teamNumber },
        });
      }
      throw notFound();
    }

    await Promise.all([
      // await the earlier queries
      teamMediaQuery,
      teamSocialsQuery,
      teamMatchesQuery,
      teamStatusesQuery,
      teamAwardsQuery,
      teamEventsQuery,
    ]);

    const endTime = Date.now();
    const duration = endTime - startTime;
    Sentry.metrics.distribution('team.page.loader.duration', duration, {
      attributes: { team_number: params.teamNumber, year },
    });

    // team needs to be returned so we can access it in meta
    return {
      teamKey,
      year,
      team,
    };
  },
  headers: publicCacheControlHeaders(),
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [
          { title: 'Team Information - The Blue Alliance' },
          {
            name: 'description',
            content: 'Team information for the FIRST Robotics Competition.',
          },
        ],
      };
    }

    const { team } = loaderData;
    const jsonLd = {
      '@context': 'https://schema.org',
      '@type': 'SportsTeam',
      name: `Team ${team.team_number} - ${team.nickname}`,
      url: `https://www.thebluealliance.com/team/${team.team_number}`,
      location: {
        '@type': 'Place',
        address: {
          '@type': 'PostalAddress',
          addressLocality: team.city,
          addressRegion: team.state_prov,
          postalCode: team.postal_code,
          addressCountry: team.country,
        },
      },
      memberOf: {
        '@type': 'SportsOrganization',
        name: 'FIRST Robotics Competition',
        url: 'https://www.firstinspires.org',
      },
    };

    return {
      meta: [
        {
          title: `${team.nickname} - Team ${team.team_number} - The Blue Alliance`,
        },
        {
          name: 'description',
          content:
            `From ${team.city}, ${team.state_prov} ${team.postal_code}, ${team.country}.` +
            ' Team information, match results, and match videos from the FIRST Robotics Competition.',
        },
      ],
      scripts: [
        {
          type: 'application/ld+json',
          children: JSON.stringify(jsonLd),
        },
      ],
    };
  },
  component: TeamPage,
});

function TeamPage(): React.JSX.Element {
  const navigate = useNavigate();
  const { teamKey, year } = Route.useLoaderData();

  const { data: team } = useSuspenseQuery(
    getTeamOptions({ path: { team_key: teamKey } }),
  );
  const { data: media } = useSuspenseQuery(
    getTeamMediaByYearOptions({ path: { team_key: teamKey, year } }),
  );
  const { data: socials } = useSuspenseQuery(
    getTeamSocialMediaOptions({ path: { team_key: teamKey } }),
  );
  const { data: yearsParticipated } = useSuspenseQuery(
    getTeamYearsParticipatedOptions({ path: { team_key: teamKey } }),
  );
  const { data: events } = useSuspenseQuery(
    getTeamEventsByYearOptions({ path: { team_key: teamKey, year } }),
  );
  const { data: matches } = useSuspenseQuery(
    getTeamMatchesByYearOptions({ path: { team_key: teamKey, year } }),
  );
  const { data: statuses } = useSuspenseQuery(
    getTeamEventsStatusesByYearOptions({ path: { team_key: teamKey, year } }),
  );
  const { data: awards } = useSuspenseQuery(
    getTeamAwardsByYearOptions({ path: { team_key: teamKey, year } }),
  );

  // sort BEFORE launching queries that depend on it
  const sortedEvents = useMemo(
    () => events.sort(sortEventsComparator),
    [events],
  );

  const eventDistrictPtsQueries = useQueries({
    queries: sortedEvents.map((e) =>
      getEventDistrictPointsOptions({ path: { event_key: e.key } }),
    ),
    combine: (results) =>
      Object.fromEntries(
        results.map((result, index) => [
          sortedEvents[index].key,
          result.data ?? null,
        ]),
      ),
  });
  const eventAlliancesQueries = useQueries({
    queries: sortedEvents.map((e) =>
      getEventAlliancesOptions({ path: { event_key: e.key } }),
    ),
    combine: (results) =>
      Object.fromEntries(
        results.map((result, index) => [
          sortedEvents[index].key,
          result.data ?? null,
        ]),
      ),
  });
  const [inView, setInView] = useState(new Set<string>());

  yearsParticipated.sort((a, b) => b - a);

  const robotPics = useMemo(
    () =>
      media
        .filter((m) => m.type === 'imgur')
        .sort((a, b) => {
          if (a.preferred) {
            return -1;
          }
          if (b.preferred) {
            return 1;
          }

          return 0;
        }),
    [media],
  );

  const maybeAvatar = useMemo(
    () => media.find((m) => m.type === 'avatar'),
    [media],
  );

  const tocItems = useMemo(
    () => [
      { slug: 'team-info', label: 'Team Info' },
      ...sortedEvents.map((e) => ({
        slug: e.key,
        label: e.short_name?.trim() ? e.short_name : e.name,
      })),
    ],
    [sortedEvents],
  );

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <TableOfContents tocItems={tocItems} inView={inView}>
        <Select
          value={String(year)}
          onValueChange={(value) => {
            void navigate({
              to: '/team/$teamNumber/{-$year}',
              params: { teamNumber: String(team.team_number), year: value },
            });
          }}
        >
          <SelectTrigger
            className="w-[120px] max-lg:h-6 max-lg:w-24 max-lg:border-none"
          >
            <SelectValue placeholder={year} />
          </SelectTrigger>
          <SelectContent className="max-h-[30vh] overflow-y-auto">
            <SelectItem value="history">History</SelectItem>
            <SelectItem value="stats">Stats</SelectItem>
            {yearsParticipated.map((y) => (
              <SelectItem key={y} value={`${y}`}>
                {y}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </TableOfContents>

      <div className="mt-8 w-full">
        <TableOfContentsSection id="team-info" setInView={setInView}>
          <div
            className="flex flex-wrap justify-center sm:flex-nowrap
              sm:justify-between"
          >
            <div className="flex flex-col justify-between">
              <div className="flex items-start">
                <div className="flex-1">
                  <TeamPageTeamInfo
                    team={team}
                    socials={socials}
                    maybeAvatar={maybeAvatar}
                  />
                </div>
                <FavoriteButton
                  modelKey={teamKey}
                  modelType={MODEL_TYPE.TEAM}
                />
              </div>
            </div>
            <div className="flex-none">
              <TeamRobotPicsCarousel media={robotPics} />
            </div>
          </div>

          <Separator className="my-4" />

          <StatsSection
            events={sortedEvents}
            team={team}
            matches={matches}
            awards={awards}
            year={year}
          />

          {awards.filter((a) => BLUE_BANNER_AWARDS.has(a.award_type)).length >
            0 && (
            <>
              <Separator className="my-4" />
              <div className="flex flex-row justify-around">
                <BlueBanners
                  awards={awards
                    .filter((a) => BLUE_BANNER_AWARDS.has(a.award_type))
                    .filter((a) => {
                      const event = sortedEvents.find(
                        (e) => e.key === a.event_key,
                      );
                      return event && SEASON_EVENT_TYPES.has(event.event_type);
                    })}
                  events={sortedEvents}
                />
              </div>
            </>
          )}
        </TableOfContentsSection>

        <div>
          <Separator className="mt-4 mb-8" />

          {sortedEvents.map((e) => (
            <TableOfContentsSection
              key={e.key}
              id={e.key}
              setInView={setInView}
            >
              <TeamEventAppearance
                event={e}
                matches={matches.filter((m) => m.event_key === e.key)}
                status={statuses[e.key]}
                team={team}
                awards={awards.filter((a) => a.event_key === e.key)}
                maybeDistrictPoints={eventDistrictPtsQueries[e.key]}
                maybeAlliances={eventAlliancesQueries[e.key]}
              />
              <Separator className="my-4" />
            </TableOfContentsSection>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatsSection({
  events,
  team,
  matches,
  awards,
  year,
}: {
  events: Event[];
  team: Team;
  matches: Match[];
  awards: Award[];
  year: number;
}) {
  const [showTable, setShowTable] = useState(false);

  const officialEvents = events.filter((e) =>
    SEASON_EVENT_TYPES.has(e.event_type),
  );
  const unofficialEvents = events.filter(
    (e) => !SEASON_EVENT_TYPES.has(e.event_type),
  );

  const officialMatches = useMemo(
    () =>
      matches.filter((m) =>
        officialEvents.map((e) => e.key).includes(m.event_key),
      ),
    [matches, officialEvents],
  );

  const unofficialMatches = useMemo(
    () =>
      matches.filter((m) =>
        unofficialEvents.map((e) => e.key).includes(m.event_key),
      ),
    [matches, unofficialEvents],
  );

  const officialRecords = useMemo(
    () => calculateTeamRecordsFromMatches(team.key, officialMatches),
    [team.key, officialMatches],
  );

  const unofficialRecords = useMemo(
    () => calculateTeamRecordsFromMatches(team.key, unofficialMatches),
    [team.key, unofficialMatches],
  );
  const officialQuals = officialRecords.quals;
  const officialPlayoff = officialRecords.playoff;
  const unofficialQuals = unofficialRecords.quals;
  const unofficialPlayoff = unofficialRecords.playoff;

  const officialRecord = addRecords(officialQuals, officialPlayoff);
  const unofficialRecord = addRecords(unofficialQuals, unofficialPlayoff);

  const combinedQuals = addRecords(officialQuals, unofficialQuals);
  const combinedPlayoff = addRecords(officialPlayoff, unofficialPlayoff);
  const combinedRecord = addRecords(combinedQuals, combinedPlayoff);

  const highScoreMatch = useMemo(
    () => getTeamsUnpenalizedHighScore(team.key, officialMatches),
    [officialMatches, team.key],
  );

  return (
    <>
      <div className="">
        Team {team.team_number} was{' '}
        <span className="font-semibold">
          {officialRecord.wins}-{officialRecord.losses}
          {officialRecord.ties > 0 ? `-${officialRecord.ties}` : ''}
        </span>{' '}
        in official play and{' '}
        <span className="font-semibold">
          {officialRecord.wins + unofficialRecord.wins}-
          {officialRecord.losses + unofficialRecord.losses}
          {officialRecord.ties + unofficialRecord.ties > 0
            ? `-${officialRecord.ties + unofficialRecord.ties}`
            : ''}
        </span>{' '}
        overall in {year}.
        <Badge
          className="ml-2 cursor-pointer"
          onClick={() => {
            setShowTable((prev) => !prev);
          }}
        >
          {showTable ? 'Hide' : 'Show'} Details
        </Badge>
      </div>

      {showTable && (
        <div>
          <div
            // The padding/margins make the separator not actually perfectly centered
            // left-47.5 looks significantly better than left-1/2
            className={`relative flex flex-wrap *:w-full before:absolute
            before:inset-y-0 before:left-[47.5%] before:hidden before:w-px
            before:bg-neutral-200 sm:mt-0 lg:*:w-1/2 lg:before:block`}
          >
            <div className="grid grid-cols-2 items-center gap-y-4">
              <Stat
                label={`Official ${pluralize(officialEvents.length, 'Event', 'Events', false)}`}
                value={officialEvents.length}
              />

              <Stat
                label={`Official ${pluralize(matches.length, 'Match', 'Matches', false)}`}
                value={officialMatches.length}
              />

              {awards.length > 0 && (
                <Stat
                  label={pluralize(awards.length, 'Award', 'Awards', false)}
                  value={awards.length}
                />
              )}

              {highScoreMatch && (
                <TooltippedStat
                  label="High Score"
                  value={highScoreMatch.score}
                  tooltip={`${highScoreMatch.match.key} - ${highScoreMatch.alliance.team_keys.map((k) => k.substring(3)).join('-')}`}
                />
              )}
            </div>

            <Table className="table-fixed [&_tr]:border-b-0">
              <TableHeader>
                <TableRow>
                  <TableHead className="text-center"></TableHead>
                  <TableHead className="text-center">Quals</TableHead>
                  <TableHead className="text-center">Playoffs</TableHead>
                  <TableHead className="text-center">Overall</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow>
                  <TableHead>Official</TableHead>
                  <RecordCell
                    record={officialRecords.quals}
                    dataTestId="official_quals"
                  />
                  <RecordCell
                    record={officialRecords.playoff}
                    dataTestId="official_playoff"
                  />
                  <RecordCell
                    record={officialRecord}
                    dataTestId="official_overall"
                  />
                </TableRow>

                <TableRow>
                  <TableHead>Unofficial</TableHead>
                  <RecordCell
                    record={unofficialRecords.quals}
                    dataTestId="unofficial_quals"
                  />
                  <RecordCell
                    record={unofficialRecords.playoff}
                    dataTestId="unofficial_playoff"
                  />
                  <RecordCell
                    record={unofficialRecord}
                    dataTestId="unofficial_overall"
                  />
                </TableRow>

                <TableRow>
                  <TableHead>Combined</TableHead>
                  <RecordCell
                    record={combinedQuals}
                    dataTestId="combined_quals"
                  />
                  <RecordCell
                    record={combinedPlayoff}
                    dataTestId="combined_playoff"
                  />
                  <RecordCell
                    record={combinedRecord}
                    dataTestId="combined_overall"
                  />
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </>
  );
}

function RecordCell({
  record,
  dataTestId,
}: {
  record: WltRecord;
  dataTestId: string;
}) {
  return (
    <TableCell className="text-center">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="cursor-pointer" data-testid={`${dataTestId}_cell`}>
              {stringifyRecord(record)}
            </div>
          </TooltipTrigger>
          <TooltipContent side="top" data-testid={`${dataTestId}_tooltip`}>
            {(winrateFromRecord(record) * 100).toFixed(0)}% winrate
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </TableCell>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div
      className="mx-auto flex min-w-[16ch] flex-col text-center"
      data-testid={`test_${label}`}
    >
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="order-first text-2xl font-semibold tracking-tight">
        {value}
      </dd>
    </div>
  );
}

function TooltippedStat({
  label,
  value,
  tooltip,
}: {
  label: string;
  value: string | number;
  tooltip: string;
}) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <Stat label={label} value={value} />
        </TooltipTrigger>
        <TooltipContent>{tooltip}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

function BlueBanners({ awards, events }: { awards: Award[]; events: Event[] }) {
  return (
    <div className="flex flex-row flex-wrap justify-center gap-2">
      {sortAwardsByEventDate(awards, events).map((a) => (
        <AwardBanner
          key={`${a.award_type}-${a.event_key}`}
          award={a}
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          event={events.find((e) => e.key === a.event_key)!}
        />
      ))}
    </div>
  );
}
