import type { AnchorHTMLAttributes, ReactNode } from 'react';

import type { Event, Match, Team } from '~/api/tba/read';
import type { TeamTooltipProps } from '~/components/tba/teamTooltip';

type AnchorProps = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
  children?: ReactNode;
};

export function Link({
  children,
  to = '',
  params = {},
  search,
  hash,
  replace: _replace,
  activeProps: _activeProps,
  ...props
}: AnchorProps & {
  to?: string;
  params?: Record<string, string | number | undefined>;
  search?: Record<string, string>;
  hash?: string;
  replace?: boolean;
  activeProps?: unknown;
}) {
  // Fills optional `/{-$name}` segments (dropped when unset), then `$name`.
  const path = to
    .replace(/\/\{-\$(\w+)\}/g, (_, name: string) =>
      params[name] === undefined ? '' : `/${params[name]}`,
    )
    .replace(/\$(\w+)/g, (_, name: string) => String(params[name] ?? ''));
  const query = search ? `?${new URLSearchParams(search).toString()}` : '';
  return (
    <a href={`${path}${query}${hash ? `#${hash}` : ''}`} {...props}>
      {children}
    </a>
  );
}

export function TeamLink({
  children,
  teamOrKey,
  year,
  ...props
}: AnchorProps & { teamOrKey: Team | string; year?: number }) {
  const teamNumber =
    typeof teamOrKey === 'string'
      ? teamOrKey.substring(3)
      : teamOrKey.team_number;
  const suffix = year === 0 ? '/history' : year ? `/${year}` : '';
  return (
    <a href={`/team/${teamNumber}${suffix}`} {...props}>
      {children}
    </a>
  );
}

export function EventLink({
  children,
  eventOrKey,
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
  children,
  matchOrKey,
  event: _event,
  noModal: _noModal,
  ...props
}: AnchorProps & {
  matchOrKey: Match | string;
  event?: Event;
  noModal?: boolean;
}) {
  const matchKey = typeof matchOrKey === 'string' ? matchOrKey : matchOrKey.key;
  return (
    <a href={`/match/${matchKey}`} {...props}>
      {children}
    </a>
  );
}

export function TeamLinkWithTooltip({
  teamKey,
  year,
  disqualified: _disqualified,
  surrogate: _surrogate,
  isWinner: _isWinner,
  isCaptain: _isCaptain,
  ...props
}: AnchorProps & TeamTooltipProps) {
  return (
    <a href={`/team/${teamKey.substring(3)}/${year}`} {...props}>
      {teamKey.substring(3)}
    </a>
  );
}
