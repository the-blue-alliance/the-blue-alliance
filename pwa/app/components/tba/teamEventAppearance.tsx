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
import { AwardBanner } from '~/components/tba/banner';
import DetailEntity from '~/components/tba/detailEntity';
import { EventLink, TeamLink } from '~/components/tba/links';
import {
  CHANGE_IN_COMP_LEVEL_BREAKER,
  END_OF_DAY_BREAKER,
  START_OF_QUALS_BREAKER,
} from '~/components/tba/match/breakers';
import SimpleMatchRowsWithBreaks from '~/components/tba/match/matchRows';
import { Badge } from '~/components/ui/badge';
import { BLUE_BANNER_AWARDS } from '~/lib/api/AwardType';
import { SEASON_EVENT_TYPES } from '~/lib/api/EventType';
import { getEventDateString } from '~/lib/eventUtils';
import { sortMatchComparator } from '~/lib/matchUtils';
import { cn, pluralize } from '~/lib/utils';

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
    <div className="flex flex-wrap gap-x-8" id={event.key}>
      <div className="w-full md:w-[32%]">
        <h2 className="text-2xl font-medium">
          <EventLink eventOrKey={event.key}>{event.name}</EventLink>
        </h2>

        <div className="mb-3 space-y-1">
          <DetailEntity icon={<DateIcon />}>
            {getEventDateString(event, 'long')}{' '}
            {event.week !== null && (
              <Badge variant={'secondary'}>Week {event.week + 1}</Badge>
            )}
          </DetailEntity>
          <DetailEntity icon={<LocationIcon />}>
            <a
              href={`https://maps.google.com/maps?q=${encodeURIComponent(`${event.city}, ${event.state_prov}, ${event.country}`)}`}
              target="_blank"
              rel="noreferrer"
            >
              {event.city}, {event.state_prov}, {event.country}
            </a>
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

        {SEASON_EVENT_TYPES.has(event.event_type) &&
          bannerAwards.length > 0 && (
            <div className="mt-6 flex flex-row flex-wrap justify-center gap-2">
              {bannerAwards.map((a) => (
                <AwardBanner key={a.award_type} award={a} event={event} />
              ))}
            </div>
          )}
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
  return (
    <div className="flow-root">
      <dl className="-my-3 divide-y divide-gray-300 text-sm">
        {status?.qual?.ranking?.rank && (
          <div className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-3 sm:gap-4">
            <dt className="font-medium">Rank</dt>
            <dd className="sm:col-span-2">
              <span className="font-bold">{status.qual.ranking.rank}</span>
              <span className="text-muted-foreground">
                {' '}
                of {status.qual.num_teams}
              </span>
            </dd>
          </div>
        )}

        {status?.qual?.ranking?.record && (
          <div className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-3 sm:gap-4">
            <dt className="font-medium">Record</dt>
            <dd className="sm:col-span-2">
              {status.qual.ranking.record.wins +
                (status.playoff?.record?.wins ?? 0)}
              -
              {status.qual.ranking.record.losses +
                (status.playoff?.record?.losses ?? 0)}
              -
              {status.qual.ranking.record.ties +
                (status.playoff?.record?.ties ?? 0)}
            </dd>
          </div>
        )}

        {awards.length > 0 && (
          <div className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-3 sm:gap-4">
            <dt className="font-medium">
              {pluralize(awards.length, 'Award', 'Awards', false)}
            </dt>
            <dd className="sm:col-span-2">
              <ul
                className={cn({
                  'list-none': awards.length == 1,
                  'list-inside list-disc': awards.length > 1,
                })}
              >
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
                      {namedRecipients.length > 0 ? (
                        <>
                          {' '}
                          ({namedRecipients.map((r) => r.awardee).join(', ')})
                        </>
                      ) : (
                        <></>
                      )}
                    </li>
                  );
                })}
              </ul>
            </dd>
          </div>
        )}

        {status?.alliance && maybeAlliances && maybeAlliances.length > 0 && (
          <div className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-3 sm:gap-4">
            <dt className="font-medium">{status.alliance.name}</dt>
            <dd className="sm:col-span-2">
              <div className="flex flex-wrap gap-1">
                {maybeAlliances
                  .find((a) => a.picks.includes(team.key))
                  ?.picks.map((k) => (
                    <TeamLink key={k} teamOrKey={k} year={event.year}>
                      <Badge key={k} variant={'outline'}>
                        {k.substring(3)}
                      </Badge>
                    </TeamLink>
                  ))}
              </div>
            </dd>
          </div>
        )}

        {maybeDistrictPoints?.points[team.key] && (
          <div className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-3 sm:gap-4">
            <dt className="font-medium">District Points</dt>
            <dd className="sm:col-span-2">
              <DistrictPointsTable
                districtPoints={maybeDistrictPoints.points[team.key]}
              />
            </dd>
          </div>
        )}
      </dl>
    </div>
  );
}

function DistrictPointsTable({
  districtPoints,
}: {
  districtPoints: EventDistrictPoints['points'][string];
}) {
  return (
    <div className="flow-root">
      <dl className="my-0 text-sm">
        <div className="grid grid-cols-3 gap-2 border-gray-200 py-0.5">
          <dt className="col-span-1 font-medium">Quals</dt>
          <dd className="col-span-2 text-right">
            {districtPoints.qual_points}
          </dd>
        </div>

        <div className="grid grid-cols-3 gap-2 border-gray-200 py-0.5">
          <dt className="col-span-1 font-medium">Alliance</dt>
          <dd className="col-span-2 text-right">
            {districtPoints.alliance_points}
          </dd>
        </div>

        <div className="grid grid-cols-3 gap-2 border-gray-200 py-0.5">
          <dt className="col-span-1 font-medium">Playoff</dt>
          <dd className="col-span-2 text-right">
            {districtPoints.elim_points}
          </dd>
        </div>

        <div className="grid grid-cols-3 gap-2 border-gray-200 py-0.5">
          <dt className="col-span-1 font-medium">Award</dt>
          <dd className="col-span-2 text-right">
            {districtPoints.award_points}
          </dd>
        </div>

        <div
          className="grid grid-cols-3 gap-2 border-t-2 border-gray-300 py-0.5
            pt-1"
        >
          <dt className="col-span-1 font-semibold">Total</dt>
          <dd className="col-span-2 text-right font-bold">
            {districtPoints.total}
          </dd>
        </div>
      </dl>
    </div>
  );
}
