import { Match } from '~/api/v3';

export function sortMatchComparator(a: Match, b: Match) {
  const compLevelValues = {
    f: 5,
    sf: 4,
    qf: 3,
    ef: 2,
    qm: 1,
  };
  if (a.comp_level !== b.comp_level) {
    return compLevelValues[a.comp_level] - compLevelValues[b.comp_level];
  }

  return a.set_number - b.set_number || a.match_number - b.match_number;
}
