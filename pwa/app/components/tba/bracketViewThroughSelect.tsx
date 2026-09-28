import { type JSX } from 'react';

import { Event, Match, PlayoffType } from '~/api/tba/read';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import { matchTitleShort } from '~/lib/matchUtils';

export const VIEW_ALL_MATCHES = 'all';

export function matchesViewedThrough(
  matches: Match[],
  viewThrough: string,
): Match[] {
  return viewThrough === VIEW_ALL_MATCHES
    ? matches
    : matches.slice(0, Number(viewThrough));
}

export default function BracketViewThroughSelect({
  matches,
  event,
  value,
  onValueChange,
}: {
  matches: Match[];
  event: Event;
  value: string;
  onValueChange: (value: string) => void;
}): JSX.Element | null {
  if (import.meta.env.PROD) {
    return null;
  }

  const items = [
    { value: VIEW_ALL_MATCHES, label: 'All matches' },
    { value: '0', label: 'Before Match 1' },
    ...matches.map((match, index) => ({
      value: String(index + 1),
      label: `View from ${matchTitleShort(match, event.playoff_type ?? PlayoffType.CUSTOM)}`,
    })),
  ];

  return (
    <Select
      items={items}
      value={value}
      onValueChange={(next) => next !== null && onValueChange(next)}
    >
      <SelectTrigger className="w-[200px]" aria-label="View from Match">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {items.map((item) => (
          <SelectItem key={item.value} value={item.value}>
            {item.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
