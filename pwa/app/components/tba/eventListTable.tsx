import { Event } from '~/api/v3';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Link } from '@remix-run/react';
import { getEventDateString } from '~/lib/utils';

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
              <div className="text-sm">
                {event.city}, {event.state_prov}, {event.country}
              </div>
            </TableCell>
            <TableCell>TODO</TableCell>
            <TableCell>{getEventDateString(event, 'short')}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
