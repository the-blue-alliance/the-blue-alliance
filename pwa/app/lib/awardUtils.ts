import { Award } from '~/api/v3';
import { AwardType, SORT_ORDER } from '~/lib/api/AwardType';

export function sortAwardsComparator(a: Award, b: Award) {
  const orderA = SORT_ORDER[a.award_type as AwardType] ?? 1000;
  const orderB = SORT_ORDER[b.award_type as AwardType] ?? 1000;
  return orderA - orderB || a.award_type - b.award_type;
}
