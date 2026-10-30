import { Link } from '@tanstack/react-router';
import { cn } from 'cn';

import MdiVideo from '~icons/mdi/video';

import { Event } from '~/api/tba/read';
import InlineIcon from '~/components/tba/inlineIcon';
import { Button, buttonVariants } from '~/components/ui/button';
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
  getEventCompactDateString,
  groupEventsByParent,
  isEventActive,
  stripParentPrefix,
} from '~/lib/eventUtils';
import { useOnlineEventWebcasts } from '~/lib/gameday/useOnlineEventWebcasts';

// Swap the space in "Apr 2" for a non-breaking one so ranges only wrap at the dash.
const keepMonthDayTogether = (dates: string) =>
  dates.replace(/(\p{L}+) (\d)/gu, '$1 $2');

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
    <Table className="w-full table-fixed">
      <TableHeader>
        <TableRow>
          <TableHead className="h-9">Event</TableHead>
          <TableHead className="hidden h-9 md:table-cell md:w-40">
            Webcast
          </TableHead>
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
          const dates = keepMonthDayTogether(getEventCompactDateString(event));
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
                className={cn('py-2 md:w-8/12 md:py-1.5', {
                  'relative pl-[26px]': isDivision,
                })}
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
                {isDivision ? (
                  <div className="text-sm text-foreground/50">{dates}</div>
                ) : (
                  <div className="text-sm text-foreground/50">
                    {event.city}, {event.state_prov}, {event.country}
                    {' · '}
                    {dates}
                  </div>
                )}
              </TableCell>
              <TableCell className="hidden md:table-cell">
                {event.webcasts.length > 0 &&
                  (isOnline || withinADay ? (
                    <a
                      href={`/gameday/${event.key}`}
                      target="_blank"
                      rel="noreferrer"
                      className={buttonVariants({
                        variant: isOnline ? 'success' : 'secondary',
                        className: 'hover:no-underline',
                      })}
                    >
                      {watchButtonContent}
                    </a>
                  ) : (
                    <Button variant="secondary" disabled>
                      {watchButtonContent}
                    </Button>
                  ))}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
