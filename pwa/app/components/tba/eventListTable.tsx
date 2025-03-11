import { Link } from 'react-router';

import MdiVideo from '~icons/mdi/video';

import { Event } from '~/api/v3';
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
import { getEventDateString } from '~/lib/eventUtils';

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
        {events.map((event) => (
          <TableRow key={event.key}>
            <TableCell className="w-8/12">
              <Link className="text-base" to={`/event/${event.key}`}>
                {event.name}
              </Link>
              <div className="text-sm text-neutral-600">
                {event.city}, {event.state_prov}, {event.country}
              </div>
            </TableCell>
            <TableCell className="mt-2 flex justify-center md:mt-1">
              {event.webcasts.length > 0 && (
                <Button className="cursor-pointer" asChild variant="success">
                  <Link
                    to={`https://www.thebluealliance.com/gameday/${event.key}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <InlineIcon iconSize="large">
                      <MdiVideo />
                      <span className="hidden md:contents">Watch Now</span>
                    </InlineIcon>
                  </Link>
                </Button>
              )}
            </TableCell>
            <TableCell>{getEventDateString(event, 'short')}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
