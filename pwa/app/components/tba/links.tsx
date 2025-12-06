import { useQueryClient } from '@tanstack/react-query';
import { Link } from '@tanstack/react-router';
import React from 'react';

import { Event, Match, Team } from '~/api/tba/read';
import { removeNonNumeric } from '~/lib/utils';

const TeamLink = React.forwardRef<
  HTMLAnchorElement,
  React.PropsWithChildren<
    {
      teamOrKey: Team | string;
      year?: number;
    } & React.AnchorHTMLAttributes<HTMLAnchorElement>
  >
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
  return (
    <Link to="/event/$eventKey" params={{ eventKey }} {...props} ref={ref} />
  );
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

const MatchLink = React.forwardRef<
  HTMLAnchorElement,
  {
    matchOrKey: Match | string;
    event?: Event;
    children: React.ReactNode;
    noModal?: boolean;
  } & React.AnchorHTMLAttributes<HTMLAnchorElement>
>(({ matchOrKey, event, children, noModal, ...props }, ref) => {
  const queryClient = useQueryClient();
  const isMatch = typeof matchOrKey !== 'string';
  const matchKey = isMatch ? matchOrKey.key : matchOrKey;

  const handleClick = () => {
    // Prepopulate the query cache with the match and event data
    if (isMatch) {
      queryClient.setQueryData(['match', matchKey], { data: matchOrKey });
    }
    if (event) {
      queryClient.setQueryData(['event', event.key], { data: event });
    }
  };

  if (noModal) {
    return (
      <Link
        to="/match/$matchKey"
        params={{ matchKey }}
        {...props}
        ref={ref}
        onClick={handleClick}
      >
        {children}
      </Link>
    );
  }

  return (
    <Link
      to="."
      search={(prev) => ({ ...prev, matchKey })}
      mask={{
        to: '/match/$matchKey',
        params: { matchKey },
        unmaskOnReload: true,
      }}
      replace={true}
      resetScroll={false}
      onClick={handleClick}
      {...props}
      ref={ref}
    >
      {children}
    </Link>
  );
});
MatchLink.displayName = 'MatchLink';

export { EventLink, LocationLink, MatchLink, TeamLink };
