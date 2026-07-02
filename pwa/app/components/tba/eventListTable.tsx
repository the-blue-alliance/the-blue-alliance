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
import {
  getEventDateString,
  groupEventsByParent,
  isEventActive,
  stripParentPrefix,
} from '~/lib/eventUtils';
import { useOnlineEventWebcasts } from '~/lib/gameday/useOnlineEventWebcasts';
import { cn } from '~/lib/utils';

const DISTRICT_COLORS: Record<string, string> = {
  ca: 'border-l-district-ca',
  chs: 'border-l-district-chs',
  fch: 'border-l-district-chs',
  fin: 'border-l-district-fin',
  in: 'border-l-district-fin',
  isr: 'border-l-district-isr',
  fim: 'border-l-district-fim',
  fma: 'border-l-district-fma',
  mar: 'border-l-district-fma',
  ne: 'border-l-district-ne',
  fnc: 'border-l-district-fnc',
  ont: 'border-l-district-ont',
  pnw: 'border-l-district-pnw',
  pch: 'border-l-district-pch',
  fsc: 'border-l-district-fsc',
  fit: 'border-l-district-fit',
  tx: 'border-l-district-fit',
  win: 'border-l-district-win',
};

function getDistrictColorClass(
  districtAbbreviation: string | undefined,
): string {
  if (!districtAbbreviation) return '';
  return DISTRICT_COLORS[districtAbbreviation.toLowerCase()] || '';
}

export default function EventListTable({
  events,
  enableGrouping = false,
}: {
  events: Event[];
  enableGrouping?: boolean;
}) {
  const isEventOnline = useOnlineEventWebcasts();
  const items = enableGrouping ? groupEventsByParent(events) : events;
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
          const districtColor = getDistrictColorClass(
            event.district?.abbreviation,
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
