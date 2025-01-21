import BiCalendar from '~icons/bi/calendar';
import BiPinMapFill from '~icons/bi/pin-map-fill';

import {
  Award,
  EliminationAlliance,
  Event,
  EventDistrictPoints,
  Match,
  Team,
  TeamEventStatus,
} from '~/api/v3';
import InlineIcon from '~/components/tba/inlineIcon';
import { EventLink, TeamLink } from '~/components/tba/links';
import MatchResultsTable from '~/components/tba/matchResultsTable';
import { Badge } from '~/components/ui/badge';
import { getEventDateString } from '~/lib/eventUtils';
import { cn, joinComponents, pluralize } from '~/lib/utils';

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
  return (
    <div className="flex flex-wrap gap-x-8 [&>*]:sm:flex-1" id={event.key}>
      <div className="w-full">
        <h2 className="text-2xl font-medium">
          <EventLink eventOrKey={event.key}>{event.name}</EventLink>
        </h2>
        <InlineIcon>
          <BiCalendar />
          {getEventDateString(event, 'long')}
          {event.week !== null && (
            <Badge variant={'secondary'} className="ml-2">
              Week {event.week + 1}
            </Badge>
          )}
        </InlineIcon>
        <InlineIcon>
          <BiPinMapFill />
          <a
            href={`https://maps.google.com/?q=${event.city}, ${event.state_prov}, ${event.country}`}
          >
            {event.city}, {event.state_prov}, {event.country}
          </a>
        </InlineIcon>

        <div className="mt-4" />

        <TeamStatus
          status={status}
          team={team}
          awards={awards}
          maybeDistrictPoints={maybeDistrictPoints}
          maybeAlliances={maybeAlliances}
        />
      </div>
      <div>
        <MatchResultsTable matches={matches} event={event} team={team} />
      </div>
    </div>
  );
}

function TeamStatus({
  status,
  team,
  awards,
  maybeDistrictPoints,
  maybeAlliances,
}: {
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
            <dt className="font-medium text-gray-900">Rank</dt>
            <dd className="text-gray-700 sm:col-span-2">
              {status.qual.ranking.rank} / {status.qual.num_teams}
            </dd>
          </div>
        )}

        {status?.qual?.ranking?.record && (
          <div className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-3 sm:gap-4">
            <dt className="font-medium text-gray-900">Record</dt>
            <dd className="text-gray-700 sm:col-span-2">
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
            <dt className="font-medium text-gray-900">
              {pluralize(awards.length, 'Award', 'Awards', false)}
            </dt>
            <dd className="text-gray-700 sm:col-span-2">
              <ul
                className={cn({
                  'list-none': awards.length == 1,
                  'list-disc': awards.length > 1,
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
            <dt className="font-medium text-gray-900">
              {status.alliance.name}
            </dt>
            <dd className="text-gray-700 sm:col-span-2">
              {joinComponents(
                maybeAlliances
                  .find((a) => a.picks.includes(team.key))
                  ?.picks.map((k) => (
                    <TeamLink key={k} teamOrKey={k}>
                      {k.substring(3)}
                    </TeamLink>
                  )) ?? [],
                '-',
              )}
            </dd>
          </div>
        )}

        {maybeDistrictPoints?.points[team.key] && (
          <div className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-3 sm:gap-4">
            <dt className="font-medium text-gray-900">District Points</dt>
            <dd className="text-gray-700 sm:col-span-2">
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
      <dl className="-my-0 divide-y divide-gray-200 text-sm">
        <div className="grid grid-cols-1 gap-1 py-1 sm:grid-cols-3 sm:gap-4">
          <dt className="font-medium text-gray-900">Quals</dt>
          <dd className="text-gray-700 sm:col-span-2">
            {districtPoints.qual_points}
          </dd>
        </div>

        <div className="grid grid-cols-1 gap-1 py-1 sm:grid-cols-3 sm:gap-4">
          <dt className="font-medium text-gray-900">Alliance</dt>
          <dd className="text-gray-700 sm:col-span-2">
            {districtPoints.alliance_points}
          </dd>
        </div>

        <div className="grid grid-cols-1 gap-1 py-1 sm:grid-cols-3 sm:gap-4">
          <dt className="font-medium text-gray-900">Playoff</dt>
          <dd className="text-gray-700 sm:col-span-2">
            {districtPoints.elim_points}
          </dd>
        </div>

        <div className="grid grid-cols-1 gap-1 py-1 sm:grid-cols-3 sm:gap-4">
          <dt className="font-medium text-gray-900">Award</dt>
          <dd className="text-gray-700 sm:col-span-2">
            {districtPoints.award_points}
          </dd>
        </div>

        <div className="grid grid-cols-1 gap-1 py-1 sm:grid-cols-3 sm:gap-4">
          <dt className="font-medium text-gray-900">Total</dt>
          <dd className="font-bold text-gray-700 sm:col-span-2">
            {districtPoints.total}
          </dd>
        </div>
      </dl>
    </div>
  );
}
