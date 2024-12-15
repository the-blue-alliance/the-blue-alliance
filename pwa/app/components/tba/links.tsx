import { Link } from '@remix-run/react';
import React from 'react';

import { Event, Team } from '~/api/v3';
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

export { TeamLink, EventLink };
