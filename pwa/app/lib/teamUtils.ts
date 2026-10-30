import { Team } from '~/api/tba/read';
import { removeNonNumeric } from '~/lib/utils';

const FIRST_AVATAR_YEAR = 2018;

export function avatarYearForTeamPage(
  year: number,
  yearsParticipated: number[] | null,
  currentSeason: number,
): number {
  if (year >= FIRST_AVATAR_YEAR) {
    return year;
  }
  return yearsParticipated?.length
    ? Math.max(...yearsParticipated)
    : currentSeason;
}

export function sortTeamsComparator(a: Team, b: Team) {
  return a.team_number - b.team_number;
}

export function sortTeamKeysComparator(a: string, b: string) {
  return Number(removeNonNumeric(a)) - Number(removeNonNumeric(b));
}

export function sortTeams(teams: Team[]) {
  return teams.toSorted(sortTeamsComparator);
}

const FAMILY_COMMUNITY = 'Family/Community';

// Words that mark text as a school rather than a company.
const SCHOOL_WORD =
  /\b(school|schools|academy|college|university|institute|HS)\b/i;

// Names look like `Sponsor/Sponsor&School&School`, but '/' and '&' also appear
// inside real names ("PG&E", "Jr/Sr High School"). Removing the known
// school_name first is reliable; without it we fall back to guessing.
export function attemptToParseSponsors(
  teamName: string,
  schoolName?: string | null,
): string[] {
  const withoutSchools = schoolName
    ? removeSchools(teamName, schoolName)
    : null;
  return withoutSchools === null
    ? parseWithoutSchoolName(teamName)
    : splitKnownSponsors(withoutSchools);
}

function splitKnownSponsors(text: string): string[] {
  const sections = text.split('/');
  const lastSection = sections.pop() ?? '';
  // A school missing from school_name can stay glued to the last sponsor
  // ("Products&Holland High School"); cut at an '&' followed by a school word.
  const schoolStart = ampersandIndexes(lastSection).find(
    (index) =>
      !isEmbeddedAmpersand(lastSection, index) &&
      !isSpacedAmpersand(lastSection, index) &&
      SCHOOL_WORD.test(lastSection.slice(index + 1)),
  );
  sections.push(
    schoolStart === undefined ? lastSection : lastSection.slice(0, schoolStart),
  );
  return sections.map((s) => s.trim()).filter((s) => s.length > 0);
}

// school_name joins schools with ' & ', in any order, so remove each separately
// if the whole string isn't found. Null if any school is missing.
function removeSchools(teamName: string, schoolName: string): string | null {
  const withoutWholeName = removeSchool(teamName, schoolName.trim());
  if (withoutWholeName !== null) return withoutWholeName;
  return schoolName
    .split(' & ')
    .reduce<string | null>(
      (rest, school) =>
        rest === null ? null : removeSchool(rest, school.trim()),
      teamName,
    );
}

// Removes a school and its separator. It must sit between separators, so
// "International School" isn't cut out of "International School PTSA".
// Searches from the end since schools come after sponsors.
function removeSchool(text: string, school: string): string | null {
  if (school.length === 0) return null;
  let at = text.lastIndexOf(school);
  while (at >= 0) {
    const before = text.slice(0, at).trimEnd();
    const after = text.slice(at + school.length).trimStart();
    // Starts the name, follows an '&', or is the last '/' section.
    const startsClean =
      before === '' ||
      before.endsWith('&') ||
      (after === '' && before.endsWith('/'));
    // Ends the name or precedes another school.
    const endsClean = after === '' || after.startsWith('&');
    if (startsClean && endsClean) {
      // Drop the separator before the school, or after it if it came first.
      const head = /[&/]$/.test(before)
        ? before.slice(0, -1).trimEnd()
        : before;
      const tail = after.replace(/^&\s*/, before === '' ? '' : '&');
      return head + tail;
    }
    at = at === 0 ? -1 : text.lastIndexOf(school, at - 1);
  }
  return null;
}

// Fallback when school_name is missing or not found in the name.
function parseWithoutSchoolName(teamName: string): string[] {
  // Strip the "Family/Community" placeholder (its '/' looks like a sponsor
  // separator) between '&'s, keep one '&', and collapse any '&&' left behind.
  let name = teamName
    .replace(/(^|&)\s*Family\/Community\s*(?=&|$)/g, '$1')
    .replace(/&(\s*&)+/g, '&');
  if (name.endsWith(FAMILY_COMMUNITY)) {
    name = name.slice(0, name.length - FAMILY_COMMUNITY.length);
  }

  const sections = name.split('/');
  const sponsors = sections.slice(0, -1).map((s) => s.trim());
  const lastSection = sections[sections.length - 1];
  const separatorIndex = findSeparatorAmpersand(
    lastSection,
    sections.length > 1,
  );

  if (separatorIndex > 0) {
    sponsors.push(lastSection.substring(0, separatorIndex).trim());
  }

  return sponsors.filter((s) => s.length > 0);
}

function ampersandIndexes(text: string): number[] {
  return Array.from(text.matchAll(/&/g), (match) => match.index);
}

// The separator is written "Foo&Bar" or sloppily "Foo &Bar"; "Foo & Bar" is
// more likely part of a name.
function isSpacedAmpersand(text: string, index: number): boolean {
  return /\s/.test(text[index - 1] ?? '') && /\s/.test(text[index + 1] ?? '');
}

// '&' inside an abbreviation ("PG&E", "AT&T", "2&3"): up to 3 characters
// before it and a single character after it.
function isEmbeddedAmpersand(text: string, index: number): boolean {
  const left = /[\p{L}\p{N}]*$/u.exec(text.slice(0, index))?.[0] ?? '';
  const right = /^[\p{L}\p{N}]*/u.exec(text.slice(index + 1))?.[0] ?? '';
  return left.length > 0 && left.length <= 3 && right.length === 1;
}

// Index of the '&' between the last sponsor and the schools, or -1.
// `hasSponsors` is true when a '/' proves sponsors come first.
function findSeparatorAmpersand(section: string, hasSponsors: boolean): number {
  const indexes = ampersandIndexes(section);
  if (indexes.length === 0) return -1;

  // A trailing '&' (school already stripped) is the separator.
  const last = indexes[indexes.length - 1];
  if (section.slice(last + 1).trim().length === 0) return last;

  const real = indexes.filter((index) => !isEmbeddedAmpersand(section, index));
  const tight = real.filter((index) => !isSpacedAmpersand(section, index));
  if (tight.length > 0) {
    // Without a '/', any '&' could belong to a sponsor name, so use the last.
    return hasSponsors ? tight[0] : last;
  }
  if (real.length === 0) return last;
  return hasSponsors ? real[0] : startOfTrailingSchools(section, real);
}

// Old names without '/' use spaced '&'s for everything ("Co & School & School").
// Walk back over trailing school-like segments; the first is always a sponsor.
function startOfTrailingSchools(section: string, separators: number[]): number {
  let cut = separators.length - 1;
  while (
    cut > 0 &&
    SCHOOL_WORD.test(section.slice(separators[cut - 1] + 1, separators[cut]))
  ) {
    cut--;
  }
  return separators[cut];
}

// This is used on teams that have a null school_name field, for example 1717.
export function attemptToParseSchoolNameFromOldTeamName(
  teamName: string,
): string {
  const lastAmpersand = teamName.lastIndexOf('&') + 1;
  return teamName.substring(lastAmpersand, teamName.length).trim();
}
