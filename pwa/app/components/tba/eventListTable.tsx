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
import { getEventDateString, isEventActive } from '~/lib/eventUtils';
import { useOnlineEventWebcasts } from '~/lib/gameday/useOnlineEventWebcasts';
import { cn } from '~/lib/utils';

const DISTRICT_COLORS: Record<string, string> = {
  // California
  ca: 'border-l-[#FAB604]',
  // Chesapeake
  chs: 'border-l-[#2FA4A9]',
  fch: 'border-l-[#2FA4A9]',
  // Indiana
  fin: 'border-l-[#E04B4B]',
  in: 'border-l-[#E04B4B]',
  // Israel
  isr: 'border-l-[#7DD3FC]',
  // Michigan
  fim: 'border-l-[#94A3B8]',
  // Mid-Atlantic
  fma: 'border-l-[#9A8FD1]',
  mar: 'border-l-[#9A8FD1]',
  // New England
  ne: 'border-l-[#271380]',
  // North Carolina
  fnc: 'border-l-[#7BA7D9]',
  // Ontario
  ont: 'border-l-[#4F6EF7]',
  // Pacific Northwest
  pnw: 'border-l-[#3A9D7A]',
  // Peachtree
  pch: 'border-l-[#FDB4A0]',
  // South Carolina
  fsc: 'border-l-[#4FA37A]',
  // Texas
  fit: 'border-l-[#E36A2E]',
  tx: 'border-l-[#E36A2E]',
  // Wisconsin
  win: 'border-l-[#E84393]',
};

function getDistrictColorClass(
  districtAbbreviation: string | undefined,
): string {
  if (!districtAbbreviation) return '';
  return DISTRICT_COLORS[districtAbbreviation.toLowerCase()] || '';
}

export default function EventListTable({ events }: { events: Event[] }) {
  const isEventOnline = useOnlineEventWebcasts();

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
          const withinADay = isEventActive(event);
          const isOnline = isEventOnline(event);
          const districtColor = getDistrictColorClass(
            event.district?.abbreviation,
          );
          return (
            <TableRow
              key={event.key}
              className={districtColor ? `border-l-4 ${districtColor}` : ''}
            >
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
                    asChild={isOnline || withinADay}
                    variant={isOnline ? 'success' : 'secondary'}
                    disabled={!isOnline && !withinADay}
                    className={cn({
                      'pointer-events-none opacity-50':
                        !isOnline && !withinADay,
                    })}
                  >
                    {isOnline || withinADay ? (
                      <a
                        href={`/gameday/${event.key}`}
                        target="_blank"
                        rel="noreferrer"
                        className="hover:no-underline"
                      >
                        <InlineIcon iconSize="large">
                          <MdiVideo />
                          <span className="hidden md:contents">
                            {isOnline ? 'Watch Now' : 'Offline'}
                          </span>
                        </InlineIcon>
                      </a>
                    ) : (
                      <InlineIcon iconSize="large">
                        <MdiVideo />
                        <span className="hidden md:contents">Offline</span>
                      </InlineIcon>
                    )}
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
