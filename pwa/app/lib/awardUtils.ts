import { Award, Event } from '~/api/tba';
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
      const dateA = new Date(eventA.start_date);
      const dateB = new Date(eventB.start_date);

      return dateA.getTime() - dateB.getTime();
    }

    return 0;
  });
}
