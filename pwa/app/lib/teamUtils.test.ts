import { describe, expect, test } from 'vitest';

import {
  attemptToParseSchoolNameFromOldTeamName,
  attemptToParseSponsors,
} from '~/lib/teamUtils';

describe.concurrent('attemptToParseSponsors', () => {
  test('Single school, multiple sponsors', () => {
    const teamName = 'Company 1/Company 2/Company 3&Public High School';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(3);
    expect(sponsors).toEqual(['Company 1', 'Company 2', 'Company 3']);
  });

  test('Single school, single sponsor', () => {
    const teamName = 'Company 1&Public High School';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(1);
    expect(sponsors).toEqual(['Company 1']);
  });

  test('Single school, no sponsors', () => {
    const teamName = 'Public High School';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(0);
    expect(sponsors).toEqual([]);
  });

  test('Multiple schools, multiple sponsors', () => {
    const teamName =
      'Company 1/Company 2&Public1 High School&Public2 High School';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(2);
    expect(sponsors).toEqual(['Company 1', 'Company 2']);
  });

  test('Multiple schools, single sponsor', () => {
    const teamName = 'Company 1&Public1 High School&Public2 High School';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(1);
    expect(sponsors).toEqual(['Company 1']);
  });

  // There is no simple way to distinguish this case from the single school single sponsor case
  // This should be pretty rare in the real world
  test('Multiple schools, no sponsors', () => {
    const teamName = 'Public1 High School&Public2 High School';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(1);
    expect(sponsors).toEqual(['Public1 High School']);
  });

  test('Family/Community, multiple sponsors', () => {
    const teamName = 'Company1/Company2&Family/Community';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(2);
    expect(sponsors).toEqual(['Company1', 'Company2']);
  });

  test('Family/Community, single sponsor', () => {
    const teamName = 'Company1&Family/Community';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(1);
    expect(sponsors).toEqual(['Company1']);
  });

  test('Family/Community, no sponsors', () => {
    const teamName = 'Family/Community';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(0);
    expect(sponsors).toEqual([]);
  });

  test("School team that has sponsors with '&' in name", () => {
    const teamName = 'Company 1&2/Company 3&Public High School';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(2);
    expect(sponsors).toEqual(['Company 1&2', 'Company 3']);
  });

  test("Community team that has sponsors with '&' in name", () => {
    const teamName = 'Company 1&2/Company 3&Family/Community';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(2);
    expect(sponsors).toEqual(['Company 1&2', 'Company 3']);
  });
});

describe.concurrent('attemptToParseSchoolNameFromOldTeamName', () => {
  test('Single school, multiple sponsors', () => {
    const teamName = 'Company 1/Company 2/Company 3&Public High School';
    const schoolName = attemptToParseSchoolNameFromOldTeamName(teamName);

    expect(schoolName).toEqual('Public High School');
  });

  test('Single school, single sponsor', () => {
    const teamName = 'Company 1&Public High School';
    const schoolName = attemptToParseSchoolNameFromOldTeamName(teamName);

    expect(schoolName).toEqual('Public High School');
  });

  test('Single school, no sponsors', () => {
    const teamName = 'Public High School';
    const schoolName = attemptToParseSchoolNameFromOldTeamName(teamName);

    expect(schoolName).toEqual('Public High School');
  });

  // There's no really an easy way to deal with this since sponsors may also have an ampersand in their name.
  // Due to how infrequent this should come up, it's probably ok.
  test('Multiple schools, multiple sponsors', () => {
    const teamName =
      'Company 1/Company 2/Company 3&Public1 High School&Public2 High School';
    const schoolName = attemptToParseSchoolNameFromOldTeamName(teamName);

    expect(schoolName).toEqual('Public2 High School');
  });
});
