import { LoaderFunctionArgs } from '@remix-run/node';
import {
  ClientLoaderFunctionArgs,
  Link,
  MetaFunction,
  Params,
  json,
  useLoaderData,
  useNavigate,
} from '@remix-run/react';
import { useMemo } from 'react';

import BiCalendar from '~icons/bi/calendar';
import BiGraphUp from '~icons/bi/graph-up';
import BiInfoCircleFill from '~icons/bi/info-circle-fill';
import BiLink from '~icons/bi/link';
import BiPinMapFill from '~icons/bi/pin-map-fill';

import {
  Award,
  Event,
  Match,
  Team,
  WltRecord,
  getTeam,
  getTeamAwardsByYear,
  getTeamEventsByYear,
  getTeamEventsStatusesByYear,
  getTeamMatchesByYear,
  getTeamMediaByYear,
  getTeamSocialMedia,
  getTeamYearsParticipated,
} from '~/api/v3';
import InlineIcon from '~/components/tba/inlineIcon';
import TeamAvatar from '~/components/tba/teamAvatar';
import TeamEventAppearance from '~/components/tba/teamEventAppearance';
import TeamRobotPicsCarousel from '~/components/tba/teamRobotPicsCarousel';
import TeamSocialMediaList from '~/components/tba/teamSocialMediaList';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '~/components/ui/accordion';
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
import { EventType, SEASON_EVENT_TYPES } from '~/lib/api/EventType';
import { sortEventsComparator } from '~/lib/eventUtils';
import {
  calculateTeamRecordsFromMatches,
  getTeamsUnpenalizedHighScore,
} from '~/lib/matchUtils';
import {
  attemptToParseSchoolNameFromOldTeamName,
  attemptToParseSponsors,
} from '~/lib/teamUtils';
import {
  addRecords,
  parseParamsForYearElseDefault,
  pluralize,
  stringifyRecord,
  winrateFromRecord,
} from '~/lib/utils';

async function loadData(params: Params) {
  if (params.teamNumber === undefined) {
    throw new Error('missing team number');
  }

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
    getTeam({ teamKey }),
    getTeamMediaByYear({ teamKey, year }),
    getTeamSocialMedia({ teamKey }),
    getTeamYearsParticipated({ teamKey }),
    getTeamEventsByYear({ teamKey, year }),
    getTeamMatchesByYear({ teamKey, year }),
    getTeamEventsStatusesByYear({ teamKey, year }),
    getTeamAwardsByYear({ teamKey, year }),
  ]);

  if (team.status === 404) {
    throw new Response(null, { status: 404 });
  }

  if (
    team.status !== 200 ||
    media.status !== 200 ||
    socials.status !== 200 ||
    yearsParticipated.status !== 200 ||
    events.status !== 200 ||
    matches.status !== 200 ||
    statuses.status !== 200 ||
    awards.status !== 200
  ) {
    throw new Response(null, { status: 500 });
  }

  if (!yearsParticipated.data.includes(year)) {
    throw new Response(null, { status: 404 });
  }

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
  };
}

export async function loader({ params }: LoaderFunctionArgs) {
  return json(await loadData(params));
}

export async function clientLoader({ params }: ClientLoaderFunctionArgs) {
  return await loadData(params);
}

export const meta: MetaFunction<typeof loader> = ({ data }) => {
  return [
    {
      title: `${data?.team.nickname} - Team ${data?.team.team_number} - The Blue Alliance`,
    },
    {
      name: 'description',
      content:
        `From ${data?.team.city}, ${data?.team.state_prov} ${data?.team.postal_code}, ${data?.team.country}.` +
        ' Team information, match results, and match videos from the FIRST Robotics Competition.',
    },
  ];
};

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
  } = useLoaderData<typeof loader>();

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

  const sponsors = attemptToParseSponsors(team.name);
  const schoolName =
    team.school_name ?? attemptToParseSchoolNameFromOldTeamName(team.name);

  return (
    <div className="flex flex-wrap sm:flex-nowrap">
      <div className="top-0 mr-4 pt-5 sm:sticky">
        <Select
          onValueChange={(value) => {
            navigate(`/team/${team.team_number}/${value}`);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder={year} />
          </SelectTrigger>
          <SelectContent>
            {yearsParticipated.map((y) => (
              <SelectItem key={y} value={`${y}`}>
                {y}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <TableOfContentsList className="mt-5">
          {events.map((e) => (
            <TableOfContentsItem key={e.key}>
              <TableOfContentsLink
                to="#todo_implement_me"
                replace={true}
                // isActive={inView.has(group.slug)}
              >
                {e.short_name}
              </TableOfContentsLink>
            </TableOfContentsItem>
          ))}
        </TableOfContentsList>
      </div>

      <div className="mt-5 w-full">
        <div className="flex flex-wrap justify-center sm:flex-nowrap sm:justify-between">
          <div className="flex flex-col justify-between">
            <div>
              <h1 className="mb-2.5 text-4xl">
                {maybeAvatar && <TeamAvatar media={maybeAvatar} />}
                Team {team.team_number} - {team.nickname}
              </h1>
              <InlineIcon>
                <BiPinMapFill />
                <a
                  href={`https://maps.google.com/maps?q=${team.city}, ${team.state_prov}, ${team.country}`}
                >
                  {team.city}, {team.state_prov}, {team.country}
                </a>
              </InlineIcon>

              {sponsors.length > 0 ? (
                <Accordion type="single" collapsible>
                  <AccordionItem value="item-1" className="border-0">
                    <AccordionTrigger className="justify-normal p-0 text-left font-normal">
                      <InlineIcon displayStyle={'flexless'}>
                        <BiInfoCircleFill />
                        {schoolName}
                        {sponsors.length > 0 &&
                          ` with ${pluralize(sponsors.length, ' sponsor', ' sponsors')}`}
                      </InlineIcon>
                    </AccordionTrigger>
                    <AccordionContent className="pb-0">
                      {sponsors.map((sponsor, i) => (
                        <Badge
                          className="m-px font-normal"
                          key={i}
                          variant={'secondary'}
                        >
                          {sponsor}
                        </Badge>
                      ))}
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              ) : (
                <InlineIcon displayStyle={'flexless'}>
                  <BiInfoCircleFill />
                  {schoolName}
                </InlineIcon>
              )}

              <InlineIcon>
                <BiCalendar />
                Rookie Year: {team.rookie_year}
              </InlineIcon>

              <InlineIcon>
                <BiLink />
                Details on{' '}
                <Link
                  to={`https://frc-events.firstinspires.org/team/${team.team_number}`}
                >
                  FRC Events
                </Link>
              </InlineIcon>

              <InlineIcon>
                <BiGraphUp />
                <Link to={`https://www.statbotics.io/team/${team.team_number}`}>
                  Statbotics
                </Link>
              </InlineIcon>
            </div>

            <div className="flex flex-wrap justify-center md:justify-start">
              <TeamSocialMediaList socials={socials} />
            </div>
          </div>
          <div className="flex-none">
            <TeamRobotPicsCarousel media={robotPics} />
          </div>
        </div>

        <Separator className="my-4" />

        <StatsSection
          team={team}
          matches={matches}
          awards={awards}
          events={events}
        />

        <div>
          <Separator className="mb-8 mt-4" />

          {events.map((e) => (
            <div key={e.key}>
              <TeamEventAppearance
                event={e}
                matches={matches.filter((m) => m.event_key === e.key)}
                status={statuses[e.key]}
              />
              <Separator className="my-4" />
            </div>
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
}: {
  events: Event[];
  team: Team;
  matches: Match[];
  awards: Award[];
}) {
  const officialEvents = events.filter((e) =>
    SEASON_EVENT_TYPES.has(e.event_type as EventType),
  );
  const unofficialEvents = events.filter(
    (e) => !SEASON_EVENT_TYPES.has(e.event_type as EventType),
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
    <div>
      <div
        // The padding/margins make the separator not actually perfectly centered
        // left-47.5 looks significantly better than left-1/2
        className={`relative flex flex-wrap before:absolute before:inset-y-0
        before:left-[47.5%]
        before:hidden before:w-px before:bg-gray-200 sm:mt-0 before:lg:block
        [&>*]:w-full [&>*]:lg:w-1/2`}
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

        <Separator className="my-4 sm:hidden" />

        <Table className="min-w-[300px] table-fixed [&_tr]:border-b-0">
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
              <RecordCell record={officialRecords.quals} />
              <RecordCell record={officialRecords.playoff} />
              <RecordCell record={officialRecord} />
            </TableRow>

            <TableRow>
              <TableHead>Unofficial</TableHead>
              <RecordCell record={unofficialRecords.quals} />
              <RecordCell record={unofficialRecords.playoff} />
              <RecordCell record={unofficialRecord} />
            </TableRow>

            <TableRow>
              <TableHead>Combined</TableHead>
              <RecordCell record={combinedQuals} />
              <RecordCell record={combinedPlayoff} />
              <RecordCell record={combinedRecord} />
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function RecordCell({ record }: { record: WltRecord }) {
  return (
    <TableCell className="text-center">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="cursor-pointer">{stringifyRecord(record)}</div>
          </TooltipTrigger>
          <TooltipContent side="top">
            {(winrateFromRecord(record) * 100).toFixed(0)}% winrate
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </TableCell>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="mx-auto flex min-w-[16ch] flex-col text-center">
      <dt className="text-gray-500">{label}</dt>
      <dd className="order-first text-2xl font-semibold tracking-tight text-gray-900">
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
