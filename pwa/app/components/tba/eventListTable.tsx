import { Link } from '@tanstack/react-router';

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
import { getEventDateString, isEventWithinADay } from '~/lib/eventUtils';

export default function EventListTable({ events }: { events: Event[] }) {
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
        {events.map((event) => {
          const withinADay = isEventWithinADay(event);
          return (
            <TableRow key={event.key}>
              <TableCell className="w-8/12">
                <Link
                  className="text-base"
                  to="/event/$eventKey"
                  params={{ eventKey: event.key }}
                >
                  {event.name}
                </Link>
                <div className="text-sm text-neutral-600">
                  {event.city}, {event.state_prov}, {event.country}
                </div>
              </TableCell>
              <TableCell className="mt-2 flex justify-center md:mt-1">
                {event.webcasts.length > 0 && (
                  <Button
                    asChild
                    variant={withinADay ? 'success' : 'secondary'}
                    disabled={!withinADay}
                    className={
                      !withinADay ? 'pointer-events-none opacity-50' : ''
                    }
                  >
                    <a
                      href={`/gameday/${event.key}`}
                      target="_blank"
                      rel="noreferrer"
                      className="hover:no-underline"
                      aria-disabled={!withinADay}
                      tabIndex={withinADay ? undefined : -1}
                    >
                      <InlineIcon iconSize="large">
                        <MdiVideo />
                        <span className="hidden md:contents">
                          {withinADay ? 'Watch Now' : 'Offline'}
                        </span>
                      </InlineIcon>
                    </a>
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
