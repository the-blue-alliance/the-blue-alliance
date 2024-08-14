import { Match } from '~/api/v3';

const COMP_LEVEL_SORT_ORDER = {
  f: 5,
  sf: 4,
  qf: 3,
  ef: 2,
  qm: 1,
};

export function sortMatchComparator(a: Match, b: Match) {
  if (a.comp_level !== b.comp_level) {
    return (
      COMP_LEVEL_SORT_ORDER[a.comp_level] - COMP_LEVEL_SORT_ORDER[b.comp_level]
    );
  }
  return a.set_number - b.set_number || a.match_number - b.match_number;
}
