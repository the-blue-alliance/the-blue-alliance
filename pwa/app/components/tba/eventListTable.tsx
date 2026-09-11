import { Link } from '@tanstack/react-router';
import { cn } from 'cn';

import MdiVideo from '~icons/mdi/video';

import { Event } from '~/api/tba/read';
import InlineIcon from '~/components/tba/inlineIcon';
import { Button } from '~/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { getDistrictColorBorderClass } from '~/lib/districtUtils';
import {
  getEventDateString,
  groupEventsByParent,
  isEventActive,
  stripParentPrefix,
} from '~/lib/eventUtils';
import { useOnlineEventWebcasts } from '~/lib/gameday/useOnlineEventWebcasts';

export default function EventListTable({ events }: { events: Event[] }) {
  const isEventOnline = useOnlineEventWebcasts();
  const items = groupEventsByParent(events);
  // Build a set of all division keys so we can identify division rows on the fly.
  const allDivisionKeys = new Set(items.flatMap((e) => e.division_keys));
  // Map each division key to its parent event name for display trimming.
  const divisionParentName = new Map(
    items.flatMap((e) => e.division_keys.map((key) => [key, e.name])),
  );

  return (
    <Table className="w-full">
      <TableHeader>
        <TableRow>
          <TableHead>Event</TableHead>
          <TableHead>Webcast</TableHead>
          <TableHead>Dates</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((event, idx) => {
          const isDivision = allDivisionKeys.has(event.key);
          // Used to restore the bottom border after suppressing it between sibling divisions.
          const isLastDivision =
            isDivision && !allDivisionKeys.has(items[idx + 1]?.key);
          const withinADay = isEventActive(event);
          const isOnline = isEventOnline(event);
          const districtColor = getDistrictColorBorderClass(
            event.district?.abbreviation,
          );
          const watchButtonContent = (
            <InlineIcon iconSize="large">
              <MdiVideo />
              <span className="hidden md:contents">
                {isOnline ? 'Watch Now' : 'Offline'}
              </span>
            </InlineIcon>
          );
          return (
            <TableRow
              key={event.key}
              className={cn(
                !isDivision && districtColor
                  ? `border-l-4 ${districtColor}`
                  : '',
                {
                  'bg-muted/40': isDivision,
                  'border-b border-b-border/40': isDivision && !isLastDivision,
                },
              )}
            >
              <TableCell
                className={cn('w-8/12', { 'relative pl-[26px]': isDivision })}
              >
                {isDivision && districtColor && (
                  <div
                    className={cn(
                      'absolute -inset-y-px left-4 w-0 border-l-4',
                      districtColor,
                    )}
                  />
                )}
                <Link
                  className="text-base"
                  to="/event/$eventKey"
                  params={{ eventKey: event.key }}
                >
                  {isDivision
                    ? stripParentPrefix(
                        event.name,
                        divisionParentName.get(event.key),
                      )
                    : event.name}
                </Link>
                {!isDivision && (
                  <div className="text-sm text-neutral-600">
                    {event.city}, {event.state_prov}, {event.country}
                  </div>
                )}
              </TableCell>
              <TableCell>
                {event.webcasts.length > 0 && (
                  <Button
                    render={
                      isOnline || withinADay ? (
                        <a
                          href={`/gameday/${event.key}`}
                          target="_blank"
                          rel="noreferrer"
                          className="hover:no-underline"
                        >
                          {watchButtonContent}
                        </a>
                      ) : undefined
                    }
                    variant={isOnline ? 'success' : 'secondary'}
                    disabled={!isOnline && !withinADay}
                    className={cn({
                      'pointer-events-none opacity-50':
                        !isOnline && !withinADay,
                    })}
                  >
                    {watchButtonContent}
                  </Button>
                )}
              </TableCell>
              <TableCell>{getEventDateString(event, 'short')}</TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
