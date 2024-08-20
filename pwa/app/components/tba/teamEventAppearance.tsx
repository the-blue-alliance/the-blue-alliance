import { Link } from '@remix-run/react';

import BiCalendar from '~icons/bi/calendar';
import BiPinMapFill from '~icons/bi/pin-map-fill';

import { Event, Match, TeamEventStatus } from '~/api/v3';
import InlineIcon from '~/components/tba/inlineIcon';
import MatchResultsTable from '~/components/tba/matchResultsTable';
import { Badge } from '~/components/ui/badge';
import { getEventDateString } from '~/lib/eventUtils';

export default function TeamEventAppearance({
  event,
  matches,
  status,
}: {
  event: Event;
  matches: Match[];
  status: TeamEventStatus | null;
}): JSX.Element {
  return (
    <div className="flex flex-wrap gap-x-8 [&>*]:sm:flex-1">
      <div className="">
        <h2 className="text-2xl">
          <Link to={`/event/${event.key}`}>{event.name}</Link>
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

        <div className="my-3" />

        <TeamStatus status={status} />
      </div>
      <div>
        <MatchResultsTable matches={matches} event={event} />
      </div>
    </div>
  );
}

function TeamStatus({ status }: { status: TeamEventStatus | null }) {
  // todo: build this out with better mid-event, future-event logic handling
  return (
    <div
      dangerouslySetInnerHTML={{ __html: status?.overall_status_str ?? '' }}
    />
  );
}
