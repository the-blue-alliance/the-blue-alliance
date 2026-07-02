import { Temporal } from 'temporal-polyfill';

import { Award, Event } from '~/api/tba/read';
import { SORT_ORDER } from '~/lib/api/AwardType';

export function sortAwardsComparator(a: Award, b: Award) {
  const orderA = SORT_ORDER[a.award_type] ?? 1000;
  const orderB = SORT_ORDER[b.award_type] ?? 1000;
  return orderA - orderB || a.award_type - b.award_type;
}

export function sortAwardsByEventDate(
  awards: Award[],
  events: Event[],
): Award[] {
  return awards.sort((a, b) => {
    const eventA = events.find((event) => event.key === a.event_key);
    const eventB = events.find((event) => event.key === b.event_key);

    if (eventA && eventB) {
      return Temporal.PlainDate.compare(
        Temporal.PlainDate.from(eventA.start_date),
        Temporal.PlainDate.from(eventB.start_date),
      );
    }

    return sortAwardsComparator(a, b);
  });
}
