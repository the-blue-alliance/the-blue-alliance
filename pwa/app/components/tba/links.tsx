import { useQueryClient } from '@tanstack/react-query';
import { Link } from '@tanstack/react-router';
import {
  type AnchorHTMLAttributes,
  type PropsWithChildren,
  type ReactNode,
  forwardRef,
} from 'react';

import { Event, Match, Team } from '~/api/tba/read';
import {
  getEventQueryKey,
  getMatchQueryKey,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { STATE_TO_ABBREVIATION, removeNonNumeric } from '~/lib/utils';

const TeamLink = forwardRef<
  HTMLAnchorElement,
  PropsWithChildren<
    {
      teamOrKey: Team | string;
      year?: number;
    } & AnchorHTMLAttributes<HTMLAnchorElement>
  >
>(({ teamOrKey, year, className, ...props }, ref) => {
  const teamNumber: string =
    typeof teamOrKey === 'string'
      ? removeNonNumeric(teamOrKey)
      : teamOrKey.team_number.toString();

  const yearSuffix = year === 0 ? 'history' : year?.toString();

  return (
    <Link
      to="/team/$teamNumber/{-$year}"
      params={{ teamNumber, year: yearSuffix }}
      className={className ?? 'text-foreground hover:underline'}
      {...props}
      ref={ref}
    />
  );
});
TeamLink.displayName = 'TeamLink';

const EventLink = forwardRef<
  HTMLAnchorElement,
  PropsWithChildren<
    {
      eventOrKey: Event | string;
    } & AnchorHTMLAttributes<HTMLAnchorElement>
  >
>(({ eventOrKey, ...props }, ref) => {
  const eventKey = typeof eventOrKey === 'string' ? eventOrKey : eventOrKey.key;
  return (
    <Link to="/event/$eventKey" params={{ eventKey }} {...props} ref={ref} />
  );
});
EventLink.displayName = 'EventLink';

const EventLocationLink = ({
  event,
  hideUSA = false,
  hideVenue = false,
}: {
  event: Event;
  hideUSA?: boolean;
  hideVenue?: boolean;
}) => {
  const href = `https://maps.google.com/?q=${encodeURIComponent(`${event.location_name}, ${event.address}, ${event.city}, ${event.state_prov}, ${event.country}`)}`;

  if (hideVenue) {
    return (
      <a href={href} target="_blank" rel="noreferrer">
        {event.city}, {event.state_prov}
        {hideUSA && event.country === 'USA' ? '' : `, ${event.country}`}
      </a>
    );
  }

  return (
    <span>
      <a href={href} target="_blank" rel="noreferrer">
        {event.location_name}
      </a>{' '}
      in {event.city}, {event.state_prov}
      {hideUSA && event.country === 'USA' ? '' : `, ${event.country}`}
    </span>
  );
};
EventLocationLink.displayName = 'EventLocationLink';

const TeamLocationLink = ({
  team,
  hideUSA = false,
}: {
  team: Team;
  hideUSA?: boolean;
}) => {
  const href = `https://maps.google.com/?q=${encodeURIComponent(`${team.city}, ${team.state_prov}, ${team.country}`)}`;
  const abbreviatedStateProv =
    STATE_TO_ABBREVIATION.get(team.state_prov ?? '') ?? team.state_prov;
  return (
    <a href={href} target="_blank" rel="noreferrer">
      {team.city}, {abbreviatedStateProv}
      {hideUSA && team.country === 'USA' ? '' : `, ${team.country}`}
    </a>
  );
};
TeamLocationLink.displayName = 'TeamLocationLink';

const MatchLink = forwardRef<
  HTMLAnchorElement,
  {
    matchOrKey: Match | string;
    event?: Event;
    children: ReactNode;
    noModal?: boolean;
  } & AnchorHTMLAttributes<HTMLAnchorElement>
>(({ matchOrKey, event, children, noModal, ...props }, ref) => {
  const queryClient = useQueryClient();
  const isMatch = typeof matchOrKey !== 'string';
  const matchKey = isMatch ? matchOrKey.key : matchOrKey;

  const handleClick = () => {
    // Prepopulate the query cache with the match and event data
    if (isMatch) {
      queryClient.setQueryData<Match>(
        getMatchQueryKey({ path: { match_key: matchKey } }),
        matchOrKey,
      );
    }
    if (event) {
      queryClient.setQueryData<Event>(
        getEventQueryKey({ path: { event_key: event.key } }),
        event,
      );
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

const DistrictLink = forwardRef<
  HTMLAnchorElement,
  PropsWithChildren<
    {
      districtAbbreviation: string;
      year?: number;
    } & AnchorHTMLAttributes<HTMLAnchorElement>
  >
>(({ districtAbbreviation, year, ...props }, ref) => {
  return (
    <Link
      to="/district/$districtAbbreviation/{-$year}"
      params={{
        districtAbbreviation,
        year: year?.toString(),
      }}
      {...props}
      ref={ref}
    />
  );
});
DistrictLink.displayName = 'DistrictLink';

export {
  DistrictLink,
  EventLink,
  EventLocationLink,
  MatchLink,
  TeamLink,
  TeamLocationLink,
};
