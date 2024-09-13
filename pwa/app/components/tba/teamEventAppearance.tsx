import { Link } from '@remix-run/react';

import DateIcon from '~icons/lucide/calendar-days';
import LocationIcon from '~icons/lucide/map-pin';

import { Event, Match, TeamEventStatus } from '~/api/v3';
import DetailEntity from '~/components/tba/detailEntity';
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
}): React.JSX.Element {
  return (
    <div className="flex flex-wrap gap-x-8 [&>*]:sm:flex-1">
      <div className="">
        <h2 className="text-2xl">
          <Link to={`/event/${event.key}`}>{event.name}</Link>
        </h2>

        <div className="space-y-1 mb-3">
          <DetailEntity icon={<DateIcon />}>
            {getEventDateString(event, 'long')}
            {event.week !== null && (
              <Badge variant={'secondary'} className="ml-2">
                Week {event.week + 1}
              </Badge>
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
