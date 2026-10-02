import { Team } from '~/api/tba/read';
import { removeNonNumeric } from '~/lib/utils';

export function sortTeamsComparator(a: Team, b: Team) {
  return a.team_number - b.team_number;
}

export function sortTeamKeysComparator(a: string, b: string) {
  return Number(removeNonNumeric(a)) - Number(removeNonNumeric(b));
}

export function sortTeams(teams: Team[]) {
  return teams.sort((a, b) => sortTeamsComparator(a, b));
}

export function attemptToParseSponsors(teamName: string): string[] {
  const familyCommunity = 'Family/Community';
  if (teamName.endsWith(familyCommunity)) {
    teamName = teamName.substring(0, teamName.length - familyCommunity.length);
  }

  // Split by '/' — every section except the last is a full sponsor.
  const sections = teamName.split('/');
  const sponsors = sections.slice(0, -1).map((s) => s.trim());

  // For the last section, find the '&' that separates the final sponsor
  // from the school name(s).
  const lastSection = sections[sections.length - 1];

  let separatorIndex: number;

  if (sections.length > 1) {
    // With '/' we know there are sponsors, so find the first '&' that is a
    // real separator — skipping any '&' embedded in a name (like "B&D" or
    // "2&3") where the adjacent word on both sides is a single character.
    separatorIndex = findSeparatorAmpersand(lastSection);
  } else {
    // Without '/', use the last '&' — we can't reliably distinguish
    // sponsor-internal '&' from the separator in this case.
    separatorIndex = lastSection.lastIndexOf('&');
  }

  if (separatorIndex > 0) {
    sponsors.push(lastSection.substring(0, separatorIndex).trim());
  }

  return sponsors.filter((s) => s.length > 0);
}

/**
 * Find the index of the '&' in a section that separates the last sponsor
 * from the school name(s). Returns -1 if no '&' is found.
 */
function findSeparatorAmpersand(section: string): number {
  const parts = section.split('&');
  if (parts.length <= 1) return -1;

  // If the last part is empty (school was stripped, e.g. Family/Community),
  // the trailing '&' is the separator.
  if (parts[parts.length - 1].trim().length === 0) {
    return section.lastIndexOf('&');
  }

  // Walk each '&' and return the first one where the adjacent words are not
  // both single characters.
  let pos = 0;
  for (let i = 0; i < parts.length - 1; i++) {
    pos += parts[i].length;

    const leftWord = parts[i].trim().split(/\s+/).pop() ?? '';
    const rightWord = parts[i + 1].trim().split(/\s+/)[0] ?? '';

    if (!(leftWord.length === 1 && rightWord.length === 1)) {
      return pos;
    }

    pos += 1; // skip past '&'
  }

  // Fallback: all '&' look embedded — use the last one.
  return section.lastIndexOf('&');
}

// This is used on teams that have a null school_name field, for example 1717.
export function attemptToParseSchoolNameFromOldTeamName(
  teamName: string,
): string {
  const lastAmpersand = teamName.lastIndexOf('&') + 1;
  return teamName.substring(lastAmpersand, teamName.length).trim();
}
