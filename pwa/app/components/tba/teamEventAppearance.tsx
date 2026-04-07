import DateIcon from '~icons/lucide/calendar-days';
import LocationIcon from '~icons/lucide/map-pin';

import {
  Award,
  EliminationAlliance,
  Event,
  EventDistrictPoints,
  Match,
  Team,
  TeamEventStatus,
} from '~/api/tba/read';
import AddToCalendarLinks from '~/components/tba/addToCalendarLinks';
import { AwardBanner } from '~/components/tba/banner';
import DetailEntity from '~/components/tba/detailEntity';
import { EventLink, EventLocationLink, TeamLink } from '~/components/tba/links';
import {
  CHANGE_IN_COMP_LEVEL_BREAKER,
  END_OF_DAY_BREAKER,
  START_OF_QUALS_BREAKER,
} from '~/components/tba/match/breakers';
import SimpleMatchRowsWithBreaks from '~/components/tba/match/matchRows';
import { Badge } from '~/components/ui/badge';
import { Separator } from '~/components/ui/separator';
import { BLUE_BANNER_AWARDS } from '~/lib/api/AwardType';
import { SEASON_EVENT_TYPES } from '~/lib/api/EventType';
import { getEventDateString } from '~/lib/eventUtils';
import { sortMatchComparator } from '~/lib/matchUtils';

function StatChip({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="rounded-lg bg-muted p-3 text-center">
      <div className="text-xs tracking-wide text-muted-foreground uppercase">
        {label}
      </div>
      <div className="mt-1 text-2xl leading-none font-bold">{value}</div>
      {sub && <div className="mt-1 text-xs text-muted-foreground">{sub}</div>}
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <h3
        className="text-sm font-medium tracking-wide text-muted-foreground
          uppercase"
      >
        {title}
      </h3>
      {children}
    </div>
  );
}

export default function TeamEventAppearance({
  event,
  matches,
  status,
  team,
  awards,
  maybeDistrictPoints,
  maybeAlliances,
}: {
  event: Event;
  matches: Match[];
  status: TeamEventStatus | null;
  team: Team;
  awards: Award[];
  maybeDistrictPoints: EventDistrictPoints | null;
  maybeAlliances: EliminationAlliance[] | null;
}): React.JSX.Element {
  const bannerAwards = awards.filter((a) =>
    BLUE_BANNER_AWARDS.has(a.award_type),
  );

  matches.sort(sortMatchComparator);

  return (
    <div className="relative" id={event.key}>
      <div className="flex flex-wrap gap-x-8">
        <div className="w-full md:w-[32%]">
          <h2 className="mb-1 text-2xl font-medium">
            <EventLink eventOrKey={event.key}>{event.name}</EventLink>
          </h2>

          <div className="mb-3 space-y-1">
            <DetailEntity icon={<DateIcon />}>
              {getEventDateString(event, 'long')}
              <AddToCalendarLinks event={event} />{' '}
              {event.week !== null && (
                <Badge variant={'secondary'}>Week {event.week + 1}</Badge>
              )}
            </DetailEntity>
            <DetailEntity icon={<LocationIcon />}>
              <EventLocationLink
                event={event}
                hideVenue={true}
                hideUSA={true}
              />
            </DetailEntity>
          </div>
          <TeamStatus
            event={event}
            status={status}
            team={team}
            awards={awards}
            maybeDistrictPoints={maybeDistrictPoints}
            maybeAlliances={maybeAlliances}
          />
        </div>

        <div className="grow">
          <SimpleMatchRowsWithBreaks
            matches={matches}
            event={event}
            breakers={[
              START_OF_QUALS_BREAKER,
              END_OF_DAY_BREAKER,
              CHANGE_IN_COMP_LEVEL_BREAKER,
            ]}
            focusTeamKey={team.key}
          />
        </div>
      </div>

      {SEASON_EVENT_TYPES.has(event.event_type) && bannerAwards.length > 0 && (
        <div
          className="absolute top-0 right-0 -mr-46 hidden min-[1550px]:flex
            min-[1550px]:flex-col min-[1550px]:gap-2"
        >
          {bannerAwards.map((a) => (
            <AwardBanner key={a.award_type} award={a} event={event} />
          ))}
        </div>
      )}
    </div>
  );
}

function TeamStatus({
  event,
  status,
  team,
  awards,
  maybeDistrictPoints,
  maybeAlliances,
}: {
  event: Event;
  status: TeamEventStatus | null;
  team: Team;
  awards: Award[];
  maybeDistrictPoints: EventDistrictPoints | null;
  maybeAlliances: EliminationAlliance[] | null;
}) {
  const hasRank = status?.qual?.ranking?.rank;
  const hasRecord = status?.qual?.ranking?.record;
  const hasAlliance =
    status?.alliance && maybeAlliances && maybeAlliances.length > 0;
  const hasAwards = awards.length > 0;
  const hasDistrictPoints = maybeDistrictPoints?.points[team.key];

  const sections = [];

  // Stats row (rank + record)
  if (hasRank || hasRecord) {
    sections.push(
      <div key="stats" className="grid grid-cols-2 gap-2">
        {hasRank && status?.qual?.ranking?.rank && (
          <StatChip
            label="Rank"
            value={status.qual.ranking.rank.toString()}
            sub={`of ${status.qual.num_teams}`}
          />
        )}
        {hasRecord && status?.qual?.ranking?.record && (
          <StatChip
            label="Record"
            value={`${
              status.qual.ranking.record.wins +
              (status.playoff?.record?.wins ?? 0)
            }-${
              status.qual.ranking.record.losses +
              (status.playoff?.record?.losses ?? 0)
            }-${
              status.qual.ranking.record.ties +
              (status.playoff?.record?.ties ?? 0)
            }`}
          />
        )}
      </div>,
    );
  }

  // Alliance section
  if (hasAlliance) {
    sections.push(
      <Section key="alliance" title={status.alliance?.name ?? 'Alliance'}>
        <div className="flex flex-wrap gap-1">
          {maybeAlliances
            .find((a) => a.picks.includes(team.key))
            ?.picks.map((k) => (
              <TeamLink key={k} teamOrKey={k} year={event.year}>
                <Badge variant={'outline'}>{k.substring(3)}</Badge>
              </TeamLink>
            ))}
        </div>
      </Section>,
    );
  }

  // Awards section
  if (hasAwards) {
    sections.push(
      <Section key="awards" title="Awards">
        <div className="space-y-3">
          <ul className="list-none space-y-1">
            {awards.map((award) => {
              const namedRecipients = award.recipient_list.filter(
                (r) =>
                  r.awardee !== null &&
                  r.awardee !== '' &&
                  r.team_key === team.key,
              );

              return (
                <li key={`${award.award_type}-${award.event_key}`}>
                  {award.name}
                  {namedRecipients.length > 0 && (
                    <span className="text-muted-foreground">
                      {' '}
                      ({namedRecipients.map((r) => r.awardee).join(', ')})
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      </Section>,
    );
  }

  // District Points section
  if (hasDistrictPoints) {
    sections.push(
      <Section key="district" title="District Points">
        <DistrictPointsTable
          districtPoints={maybeDistrictPoints.points[team.key]}
        />
      </Section>,
    );
  }

  if (sections.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      {sections.map((section, index) => (
        <div key={section.key}>
          {index > 0 && <Separator className="mb-4" />}
          {section}
        </div>
      ))}
    </div>
  );
}

function DistrictPointsTable({
  districtPoints,
}: {
  districtPoints: EventDistrictPoints['points'][string];
}) {
  return (
    <div className="space-y-1 text-sm">
      <div className="flex justify-between">
        <span>Quals</span>
        <span className="font-medium">{districtPoints.qual_points}</span>
      </div>
      <div className="flex justify-between">
        <span>Alliance</span>
        <span className="font-medium">{districtPoints.alliance_points}</span>
      </div>
      <div className="flex justify-between">
        <span>Playoff</span>
        <span className="font-medium">{districtPoints.elim_points}</span>
      </div>
      <div className="flex justify-between">
        <span>Award</span>
        <span className="font-medium">{districtPoints.award_points}</span>
      </div>
      <Separator className="my-2" />
      <div className="flex justify-between font-semibold">
        <span>Total</span>
        <span>{districtPoints.total}</span>
      </div>
    </div>
  );
}
