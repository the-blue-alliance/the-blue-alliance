import { useMemo, useState } from 'react';
import { InView } from 'react-intersection-observer';
import { useLoaderData, useNavigate } from 'react-router';

import {
  Award,
  EliminationAlliance,
  Event,
  EventDistrictPoints,
  Match,
  Team,
  WltRecord,
  getEventAlliances,
  getEventDistrictPoints,
  getTeam,
  getTeamAwardsByYear,
  getTeamEventsByYear,
  getTeamEventsStatusesByYear,
  getTeamMatchesByYear,
  getTeamMediaByYear,
  getTeamSocialMedia,
  getTeamYearsParticipated,
} from '~/api/tba/read';
import { AwardBanner } from '~/components/tba/banner';
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
  TableOfContentsItem,
  TableOfContentsLink,
  TableOfContentsList,
} from '~/components/ui/toc';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import { BLUE_BANNER_AWARDS } from '~/lib/api/AwardType';
import { EventType, SEASON_EVENT_TYPES } from '~/lib/api/EventType';
import { sortAwardsByEventDate } from '~/lib/awardUtils';
import { sortEventsComparator } from '~/lib/eventUtils';
import {
  calculateTeamRecordsFromMatches,
  getTeamsUnpenalizedHighScore,
} from '~/lib/matchUtils';
import {
  addRecords,
  parseParamsForYearElseDefault,
  pluralize,
  stringifyRecord,
  winrateFromRecord,
} from '~/lib/utils';

import { Route } from '.react-router/types/app/routes/+types/team.$teamNumber.($year)';

async function loadData(params: Route.LoaderArgs['params']) {
  const teamKey = `frc${params.teamNumber}`;
  const year = await parseParamsForYearElseDefault(params);
  if (year === undefined) {
    throw new Response(null, { status: 404 });
  }

  const [
    team,
    media,
    socials,
    yearsParticipated,
    events,
    matches,
    statuses,
    awards,
  ] = await Promise.all([
    getTeam({ path: { team_key: teamKey } }),
    getTeamMediaByYear({ path: { team_key: teamKey, year } }),
    getTeamSocialMedia({ path: { team_key: teamKey } }),
    getTeamYearsParticipated({ path: { team_key: teamKey } }),
    getTeamEventsByYear({ path: { team_key: teamKey, year } }),
    getTeamMatchesByYear({ path: { team_key: teamKey, year } }),
    getTeamEventsStatusesByYear({ path: { team_key: teamKey, year } }),
    getTeamAwardsByYear({ path: { team_key: teamKey, year } }),
  ]);

  if (team.data === undefined) {
    throw new Response(null, { status: 404 });
  }

  if (
    media.data === undefined ||
    socials.data === undefined ||
    yearsParticipated.data === undefined ||
    events.data === undefined ||
    matches.data === undefined ||
    statuses.data === undefined ||
    awards.data === undefined
  ) {
    throw new Response(null, { status: 500 });
  }

  if (!yearsParticipated.data.includes(year)) {
    throw new Response(null, { status: 404 });
  }

  // TODO: fetch these in parallel after initial render
  const eventDistrictPts: Record<string, EventDistrictPoints | null> = {};
  await Promise.all(
    events.data.map(async (e) => {
      if (
        [
          EventType.DISTRICT,
          EventType.DISTRICT_CMP,
          EventType.DISTRICT_CMP_DIVISION,
        ].includes(e.event_type)
      ) {
        const resp = await getEventDistrictPoints({
          path: { event_key: e.key },
        });
        eventDistrictPts[e.key] = resp.data ?? null;
      } else {
        eventDistrictPts[e.key] = null;
      }
    }),
  );
  const eventAlliances: Record<string, EliminationAlliance[] | null> = {};
  await Promise.all(
    events.data.map(async (e) => {
      const resp = await getEventAlliances({ path: { event_key: e.key } });
      eventAlliances[e.key] = resp.data ?? null;
    }),
  );

  return {
    year,
    team: team.data,
    media: media.data,
    socials: socials.data,
    yearsParticipated: yearsParticipated.data,
    events: events.data,
    matches: matches.data,
    statuses: statuses.data,
    awards: awards.data,
    eventDistrictPts: eventDistrictPts,
    eventAlliances: eventAlliances,
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
        title: `Team Information - The Blue Alliance`,
      },
      {
        name: 'description',
        content: `Team information for the FIRST Robotics Competition.`,
      },
    ];
  }

  return [
    {
      title: `${data.team.nickname} - Team ${data.team.team_number} - The Blue Alliance`,
    },
    {
      name: 'description',
      content:
        `From ${data.team.city}, ${data.team.state_prov} ${data.team.postal_code}, ${data.team.country}.` +
        ' Team information, match results, and match videos from the FIRST Robotics Competition.',
    },
  ];
}

export default function TeamPage(): React.JSX.Element {
  const navigate = useNavigate();
  const {
    year,
    team,
    media,
    socials,
    yearsParticipated,
    events,
    matches,
    statuses,
    awards,
    eventDistrictPts,
    eventAlliances,
  } = useLoaderData<typeof loader>();
  const [eventsInView, setEventsInView] = useState(new Set());

  events.sort(sortEventsComparator);

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

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <div className="basis-full lg:basis-1/6">
        <div className="top-14 pt-8 sm:sticky">
          <Select
            value={String(year)}
            onValueChange={(value) => {
              void navigate(`/team/${team.team_number}/${value}`);
            }}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder={year} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="history">History</SelectItem>
              {yearsParticipated.map((y) => (
                <SelectItem key={y} value={`${y}`}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <TableOfContentsList className="mt-2">
            {events.map((e) => (
              <TableOfContentsItem key={e.key}>
                <TableOfContentsLink
                  to={`#${e.key}`}
                  replace={true}
                  isActive={eventsInView.has(e.key)}
                >
                  {e.short_name?.trim() ? e.short_name : e.name}
                </TableOfContentsLink>
              </TableOfContentsItem>
            ))}
          </TableOfContentsList>
        </div>
      </div>

      <div className="mt-8 w-full">
        <div
          className="flex flex-wrap justify-center sm:flex-nowrap
            sm:justify-between"
        >
          <div className="flex flex-col justify-between">
            <TeamPageTeamInfo
              team={team}
              socials={socials}
              maybeAvatar={maybeAvatar}
            />
          </div>
          <div className="flex-none">
            <TeamRobotPicsCarousel media={robotPics} />
          </div>
        </div>

        <Separator className="my-4" />

        <StatsSection
          events={events}
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
                    const event = events.find((e) => e.key === a.event_key);
                    return event && SEASON_EVENT_TYPES.has(event.event_type);
                  })}
                events={events}
              />
            </div>
          </>
        )}

        <div>
          <Separator className="mt-4 mb-8" />

          {events.map((e) => (
            <InView
              as="div"
              key={e.key}
              onChange={(inView) => {
                setEventsInView((prev) => {
                  if (inView) {
                    prev.add(e.key);
                  } else {
                    prev.delete(e.key);
                  }
                  return new Set(prev);
                });
              }}
            >
              <TeamEventAppearance
                event={e}
                matches={matches.filter((m) => m.event_key === e.key)}
                status={statuses[e.key]}
                team={team}
                awards={awards.filter((a) => a.event_key === e.key)}
                maybeDistrictPoints={eventDistrictPts[e.key]}
                maybeAlliances={eventAlliances[e.key]}
              />
              <Separator className="my-4" />
            </InView>
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
            before:bg-gray-200 sm:mt-0 lg:*:w-1/2 lg:before:block`}
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
      <dt className="text-gray-500">{label}</dt>
      <dd
        className="order-first text-2xl font-semibold tracking-tight
          text-gray-900"
      >
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
