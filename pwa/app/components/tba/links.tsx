import React from 'react';
import { Link } from 'react-router';

import { Event, Match, Team } from '~/api/tba/read';
import { useMatchModal } from '~/lib/matchModalContext';
import { removeNonNumeric } from '~/lib/utils';

const TeamLink = React.forwardRef<
  HTMLAnchorElement,
  React.PropsWithChildren<{
    teamOrKey: Team | string;
    year?: number;
  }>
>(({ teamOrKey, year, ...props }, ref) => {
  const teamNumber =
    typeof teamOrKey === 'string'
      ? removeNonNumeric(teamOrKey)
      : teamOrKey.team_number;

  const yearSuffix =
    year === undefined ? '' : year === 0 ? 'history' : year.toString();

  const href = `/team/${teamNumber}/${yearSuffix}`;
  return <Link to={href} {...props} ref={ref} />;
});
TeamLink.displayName = 'TeamLink';

const EventLink = React.forwardRef<
  HTMLAnchorElement,
  React.PropsWithChildren<
    {
      eventOrKey: Event | string;
    } & React.AnchorHTMLAttributes<HTMLAnchorElement>
  >
>(({ eventOrKey, ...props }, ref) => {
  const eventKey = typeof eventOrKey === 'string' ? eventOrKey : eventOrKey.key;
  return <Link to={`/event/${eventKey}`} {...props} ref={ref} />;
});
EventLink.displayName = 'EventLink';

const LocationLink = React.forwardRef<
  HTMLAnchorElement,
  React.PropsWithChildren<{
    city: string;
    state_prov: string;
    country: string;
    hideUSA?: boolean;
  }>
>(({ city, state_prov, country, hideUSA, children, ...props }, ref) => {
  const url = `https://maps.google.com/?q=${city}, ${state_prov}, ${country}`;

  return children ? (
    <Link to={url} {...props} ref={ref}>
      {children}
    </Link>
  ) : (
    <Link to={url} {...props} ref={ref}>
      {city}, {state_prov}
      {hideUSA && country === 'USA' ? '' : `, ${country}`}
    </Link>
  );
});
LocationLink.displayName = 'LocationLink';

interface MatchLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  match: Match;
  event: Event;
  children: React.ReactNode;
}

const MatchLink = React.forwardRef<HTMLAnchorElement, MatchLinkProps>(
  ({ match, event, children, onClick, ...props }, ref) => {
    const { openMatch } = useMatchModal();

    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
      e.preventDefault();
      openMatch(match, event);
      onClick?.(e);
    };

    return (
      <Link
        to={`/match/${match.key}`}
        onClick={handleClick}
        ref={ref}
        {...props}
      >
        {children}
      </Link>
    );
  },
);
MatchLink.displayName = 'MatchLink';

export { TeamLink, EventLink, LocationLink, MatchLink };
