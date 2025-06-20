import React from 'react';
import { Link } from 'react-router';

import { Event, Team } from '~/api/tba/read';
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
  React.PropsWithChildren<{
    eventOrKey: Event | string;
  }>
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

export { TeamLink, EventLink, LocationLink };
