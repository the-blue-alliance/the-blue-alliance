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

const DISTRICT_COLORS: Record<string, string> = {
  // California
  ca: 'shadow-[inset_4px_0_0_0_#FAB604]',
  // Chesapeake
  chs: 'shadow-[inset_4px_0_0_0_#2FA4A9]',
  fch: 'shadow-[inset_4px_0_0_0_#2FA4A9]',
  // Indiana
  fin: 'shadow-[inset_4px_0_0_0_#E04B4B]',
  in: 'shadow-[inset_4px_0_0_0_#E04B4B]',
  // Israel
  isr: 'shadow-[inset_4px_0_0_0_#7DD3FC]',
  // Michigan
  fim: 'shadow-[inset_4px_0_0_0_#94A3B8]',
  // Mid-Atlantic
  fma: 'shadow-[inset_4px_0_0_0_#9A8FD1]',
  mar: 'shadow-[inset_4px_0_0_0_#9A8FD1]',
  // New England
  ne: 'shadow-[inset_4px_0_0_0_#271380]',
  // North Carolina
  fnc: 'shadow-[inset_4px_0_0_0_#7BA7D9]',
  // Ontario
  ont: 'shadow-[inset_4px_0_0_0_#4F6EF7]',
  // Pacific Northwest
  pnw: 'shadow-[inset_4px_0_0_0_#3A9D7A]',
  // Peachtree
  pch: 'shadow-[inset_4px_0_0_0_#FDB4A0]',
  // South Carolina
  fsc: 'shadow-[inset_4px_0_0_0_#4FA37A]',
  // Texas
  fit: 'shadow-[inset_4px_0_0_0_#E36A2E]',
  tx: 'shadow-[inset_4px_0_0_0_#E36A2E]',
  // Wisconsin
  wi: 'shadow-[inset_4px_0_0_0_#5FAF8C]',
};

function getDistrictColorClass(
  districtAbbreviation: string | undefined,
): string {
  if (!districtAbbreviation) return '';
  const shadow = DISTRICT_COLORS[districtAbbreviation.toLowerCase()];
  return shadow ? `${shadow} [&>td:first-child]:pl-2` : '';
}

export default function EventListTable({ events }: { events: Event[] }) {
  return (
    <Table className="w-full" wrapperClassName="overflow-visible">
      <TableHeader
        className="sticky top-[6.5rem] z-1 bg-background
          shadow-[0_1px_0_0_var(--color-border)]"
      >
        <TableRow>
          <TableHead>Event</TableHead>
          <TableHead>Webcast</TableHead>
          <TableHead>Dates</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {events.map((event) => {
          const withinADay = isEventWithinADay(event);
          const districtColor = getDistrictColorClass(
            event.district?.abbreviation,
          );
          return (
            <TableRow key={event.key} className={districtColor}>
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
