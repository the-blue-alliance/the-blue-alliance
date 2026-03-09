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

  const lastSlash = Math.max(teamName.lastIndexOf('/'), 0);
  const lastAmpersand = teamName.substring(lastSlash).lastIndexOf('&');
  const sponsorCompanySection = teamName.substring(
    0,
    lastSlash + lastAmpersand,
  );

  const sponsors = sponsorCompanySection
    .split('/')
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
  return sponsors;
}

// This is used on teams that have a null school_name field, for example 1717.
export function attemptToParseSchoolNameFromOldTeamName(
  teamName: string,
): string {
  const lastAmpersand = teamName.lastIndexOf('&') + 1;
  return teamName.substring(lastAmpersand, teamName.length).trim();
}
