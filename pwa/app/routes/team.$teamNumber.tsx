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
import React, { useMemo } from 'react';

import BiCalendar from '~icons/bi/calendar';
import BiGraphUp from '~icons/bi/graph-up';
import BiInfoCircleFill from '~icons/bi/info-circle-fill';
import BiLink from '~icons/bi/link';
import BiPinMapFill from '~icons/bi/pin-map-fill';

import {
  getTeam,
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
  TableOfContentsItem,
  TableOfContentsLink,
  TableOfContentsList,
} from '~/components/ui/toc';
import { EventType, SEASON_EVENT_TYPES } from '~/lib/api/EventType';
import { sortEventsComparator } from '~/lib/eventUtils';
import { calculateTeamRecordFromMatches } from '~/lib/matchUtils';
import {
  attemptToParseSchoolNameFromOldTeamName,
  attemptToParseSponsors,
} from '~/lib/teamUtils';
import { pluralize, stringifyRecord } from '~/lib/utils';

async function loadData(params: Params) {
  if (params.teamNumber === undefined) {
    throw new Error('missing team number');
  }

  const teamKey = `frc${params.teamNumber}`;
  // todo: add year support
  const year = 2024;

  const [team, media, socials, yearsParticipated, events, matches, statuses] =
    await Promise.all([
      getTeam({ teamKey }),
      getTeamMediaByYear({ teamKey, year }),
      getTeamSocialMedia({ teamKey }),
      getTeamYearsParticipated({ teamKey }),
      getTeamEventsByYear({ teamKey, year }),
      getTeamMatchesByYear({ teamKey, year }),
      getTeamEventsStatusesByYear({ teamKey, year }),
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
    statuses.status !== 200
  ) {
    throw new Response(null, { status: 500 });
  }

  return {
    team: team.data,
    media: media.data,
    socials: socials.data,
    yearsParticipated: yearsParticipated.data,
    events: events.data,
    matches: matches.data,
    statuses: statuses.data,
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

export default function TeamPage(): JSX.Element {
  const navigate = useNavigate();
  const { team, media, socials, yearsParticipated, events, matches, statuses } =
    useLoaderData<typeof loader>();

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

  const officialEvents = events.filter((e) =>
    SEASON_EVENT_TYPES.has(e.event_type as EventType),
  );
  const unofficialEvents = events.filter(
    (e) => !SEASON_EVENT_TYPES.has(e.event_type as EventType),
  );

  const officialRecord = useMemo(
    () =>
      calculateTeamRecordFromMatches(
        team.key,
        matches.filter((m) =>
          officialEvents.map((e) => e.key).includes(m.event_key),
        ),
      ),
    [matches, team.key, officialEvents],
  );
  const unofficialRecord = useMemo(
    () =>
      calculateTeamRecordFromMatches(
        team.key,
        matches.filter((m) =>
          unofficialEvents.map((e) => e.key).includes(m.event_key),
        ),
      ),
    [matches, team.key, unofficialEvents],
  );

  return (
    <div className="flex flex-wrap sm:flex-nowrap">
      <div className="top-0 mr-4 pt-5 sm:sticky">
        <Select
          onValueChange={(value) => {
            navigate(`/team/${team.team_number}/${value}`);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder={yearsParticipated[0]} />
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

        <div>
          <StatsBlock>
            <Stat
              label={`Official ${pluralize(officialEvents.length, 'Event', 'Events', false)}`}
              value={officialEvents.length}
            />
            {unofficialEvents.length > 0 && (
              <Stat
                label={`Unofficial ${pluralize(unofficialEvents.length, 'Event', 'Events', false)}`}
                value={unofficialEvents.length}
              />
            )}

            <Stat
              label="Official Record"
              value={stringifyRecord(officialRecord)}
            />

            {unofficialEvents.length > 0 &&
              unofficialRecord.wins +
                unofficialRecord.losses +
                unofficialRecord.ties >
                0 && (
                <>
                  <Stat
                    label="Unofficial Record"
                    value={stringifyRecord(unofficialRecord)}
                  />

                  <Stat
                    label="Overall Record"
                    value={stringifyRecord({
                      wins: officialRecord.wins + unofficialRecord.wins,
                      losses: officialRecord.losses + unofficialRecord.losses,
                      ties: officialRecord.ties + unofficialRecord.ties,
                    })}
                  />
                </>
              )}
          </StatsBlock>

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

function StatsBlock({
  children,
}: {
  children: React.ReactNode | React.ReactNode[];
}) {
  return <dl className="flex flex-wrap justify-center gap-4">{children}</dl>;
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="mx-auto flex w-[calc(50%-0.5rem)] min-w-[14ch] flex-col text-center sm:w-[calc(20%-0.8rem)]">
      <dt className="text-gray-500">{label}</dt>
      <dd className="order-first text-3xl font-semibold tracking-tight text-gray-900">
        {value}
      </dd>
    </div>
  );
}
