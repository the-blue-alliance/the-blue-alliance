import { Team } from '~/api/v3';

import { removeNonNumeric } from './utils';

export function sortTeamsComparator(a: Team, b: Team) {
  return a.team_number - b.team_number;
}

export function sortTeamKeysComparator(a: string, b: string) {
  return Number(removeNonNumeric(a)) - Number(removeNonNumeric(b));
}
