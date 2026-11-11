import type { AnchorHTMLAttributes } from 'react';

import type { Event, Match, Team } from '~/api/tba/read';

type AnchorProps = AnchorHTMLAttributes<HTMLAnchorElement>;

function withYear(path: string, year: number | undefined) {
  return year === undefined ? path : `${path}/${year}`;
}

export function TeamLink({
  teamOrKey,
  year,
  children,
  ...props
}: AnchorProps & { teamOrKey: Team | string; year?: number }) {
  const teamNumber =
    typeof teamOrKey === 'string'
      ? teamOrKey.replace(/\D/g, '')
      : teamOrKey.team_number;
  const href =
    year === 0
      ? `/team/${teamNumber}/history`
      : withYear(`/team/${teamNumber}`, year);
  return (
    <a href={href} {...props}>
      {children}
    </a>
  );
}

export function EventLink({
  eventOrKey,
  children,
  ...props
}: AnchorProps & { eventOrKey: Event | string }) {
  const eventKey = typeof eventOrKey === 'string' ? eventOrKey : eventOrKey.key;
  return (
    <a href={`/event/${eventKey}`} {...props}>
      {children}
    </a>
  );
}

export function MatchLink({
  matchOrKey,
  event,
  noModal: _noModal,
  children,
  ...props
}: AnchorProps & {
  matchOrKey: Match | string;
  event?: Event;
  noModal?: boolean;
}) {
  const matchKey = typeof matchOrKey === 'string' ? matchOrKey : matchOrKey.key;
  return (
    <a href={`/match/${matchKey}`} data-event={event?.key} {...props}>
      {children}
    </a>
  );
}

export function DistrictLink({
  districtAbbreviation,
  year,
  children,
  ...props
}: AnchorProps & { districtAbbreviation: string; year?: number }) {
  return (
    <a href={withYear(`/district/${districtAbbreviation}`, year)} {...props}>
      {children}
    </a>
  );
}

export function EventLocationLink({ event }: { event: Event }) {
  return <a href="#map">{event.city}</a>;
}

export function TeamLocationLink({ team }: { team: Team }) {
  return <a href="#map">{team.city}</a>;
}
