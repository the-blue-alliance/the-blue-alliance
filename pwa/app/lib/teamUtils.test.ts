import { describe, expect, test } from 'vitest';

import type { Team } from '~/api/tba/read';
import {
  attemptToParseSchoolNameFromOldTeamName,
  attemptToParseSponsors,
  sortTeamKeysComparator,
  sortTeams,
  sortTeamsComparator,
} from '~/lib/teamUtils';

describe('attemptToParseSponsors', () => {
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
    expect(sponsors).toEqual(['Company 1&Public1 High School']);
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

  test("Last sponsor has '&' in name (with spaces)", () => {
    const teamName = 'Company 1/Company 2 & 3&Public School';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(2);
    expect(sponsors).toEqual(['Company 1', 'Company 2 & 3']);
  });

  test("Last sponsor has '&' in name (no spaces)", () => {
    const teamName = 'Company 1/Company 2&3&Public School';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(2);
    expect(sponsors).toEqual(['Company 1', 'Company 2&3']);
  });

  test("Community team that has sponsors with '&' in name", () => {
    const teamName = 'Company 1&2/Company 3&Family/Community';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(2);
    expect(sponsors).toEqual(['Company 1&2', 'Company 3']);
  });

  // Tests with real team names to verify the parsing works as expected in the real world
  test('1741 (1 school, many sponsors)', () => {
    const teamName =
      'Crossroads Engineers/The Poul Due Jensen Foundation (Peerless Pump Company)/Toyota Materials Handling (TMH)/Center Grove Education Foundation/Cummins Inc./Red Alert Robotics Parent Organization&Center Grove High School';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(6);
    expect(sponsors).toEqual([
      'Crossroads Engineers',
      'The Poul Due Jensen Foundation (Peerless Pump Company)',
      'Toyota Materials Handling (TMH)',
      'Center Grove Education Foundation',
      'Cummins Inc.',
      'Red Alert Robotics Parent Organization',
    ]);
  });

  test('3940 (1 school, many sponsors, & in last sponsor name)', () => {
    const teamName =
      'AndyMark, Inc./Aptiv/Swerve Drive Specialties/B&D Manufacturing&Northwestern High School';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(4);
    expect(sponsors).toEqual([
      'AndyMark, Inc.',
      'Aptiv',
      'Swerve Drive Specialties',
      'B&D Manufacturing',
    ]);
  });

  test('1717 (1 school, many sponsors, & in many sponsor names)', () => {
    const teamName =
      "Raytheon/Mosher Foundation/Outhwaite Foundation/Valley Precision Products/lynda.com/P&G Alumni Association/Neal Feay Company/Edison International/Rincon Engineering/Amgen Foundation/ATK Space/Tecolote Research, Inc./Allergan Foundation/Downey's/Lockheed Martin/Enerpro, Inc./Toyon Research Corporation/FLIR/Montecito Bank & Trust/Rincon Technology/Las Cumbres Observatory Global Telescope/Citrix Online/Impulse Advanced Communications/AFAR Communications Inc./Silvergreens/City of Goleta/Santa Barbara County ROP & DOS PUEBLOS SENIOR HIGH";
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(27);
    expect(sponsors).toEqual([
      'Raytheon',
      'Mosher Foundation',
      'Outhwaite Foundation',
      'Valley Precision Products',
      'lynda.com',
      'P&G Alumni Association',
      'Neal Feay Company',
      'Edison International',
      'Rincon Engineering',
      'Amgen Foundation',
      'ATK Space',
      'Tecolote Research, Inc.',
      'Allergan Foundation',
      "Downey's",
      'Lockheed Martin',
      'Enerpro, Inc.',
      'Toyon Research Corporation',
      'FLIR',
      'Montecito Bank & Trust',
      'Rincon Technology',
      'Las Cumbres Observatory Global Telescope',
      'Citrix Online',
      'Impulse Advanced Communications',
      'AFAR Communications Inc.',
      'Silvergreens',
      'City of Goleta',
      'Santa Barbara County ROP',
    ]);
  });

  test('8724 (Family/Community, many sponsors, & in last sponsor name)', () => {
    const teamName =
      'Wire Belt Company of America/Gene Haas Foundation/BAE/TE Connectivity/REVO Casino & Social House&Family/Community';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(5);
    expect(sponsors).toEqual([
      'Wire Belt Company of America',
      'Gene Haas Foundation',
      'BAE',
      'TE Connectivity',
      'REVO Casino & Social House',
    ]);
  });

  test('308 (Many schools, many sponsors)', () => {
    const teamName =
      'BVA Oils/GM/Rockwell Automation/Michigan Department of Education&Walled Lake Northern High Sch&Walled Lake Central High Sch&Walled Lake Western High Sch';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(4);
    expect(sponsors).toEqual([
      'BVA Oils',
      'GM',
      'Rockwell Automation',
      'Michigan Department of Education',
    ]);
  });

  test('359 (Many schools, many sponsors, & in sponsor names)', () => {
    const teamName =
      'State of Hawaii Dream Equipment Dream Fund - 1,800,000.00/State of Hawaii CIP/State of Hawaii Title IV-A SSAE Grant/State of Hawaii DHS Uplink Grant /Waialua Complex 21st CCLC Grant /Friends of Waialua Robotics, Inc. /McInerny Foundation /Waialua High School STEM Learning Center /PHNSY & IMF /Career & Technical Education - Perkins and State /Atherton Family Foundation/First Hawaiian Bank Foundation /Corteva Agriscience /L3 Harris Foundation /Waialua Federal Credit Union/Gene Haas Foundation /RTX-Raytheon /NFL Foundation /Ms. Fumiko Horii /Susan L. Smith Charitable Fund /Hawaiian Electric Company /BAE Systems P&S /Island X Hawaii /HawaiiUSA Federal Credit Union Foundation /Oakley, Inc./Individual Sponsors and Families/Armed Forces Communications and Electronics Association - AFCEA International &Waialua High & Interm School';
    const sponsors = attemptToParseSponsors(teamName);

    expect(sponsors.length).toEqual(27);
    expect(sponsors).toEqual([
      'State of Hawaii Dream Equipment Dream Fund - 1,800,000.00',
      'State of Hawaii CIP',
      'State of Hawaii Title IV-A SSAE Grant',
      'State of Hawaii DHS Uplink Grant',
      'Waialua Complex 21st CCLC Grant',
      'Friends of Waialua Robotics, Inc.',
      'McInerny Foundation',
      'Waialua High School STEM Learning Center',
      'PHNSY & IMF',
      'Career & Technical Education - Perkins and State',
      'Atherton Family Foundation',
      'First Hawaiian Bank Foundation',
      'Corteva Agriscience',
      'L3 Harris Foundation',
      'Waialua Federal Credit Union',
      'Gene Haas Foundation',
      'RTX-Raytheon',
      'NFL Foundation',
      'Ms. Fumiko Horii',
      'Susan L. Smith Charitable Fund',
      'Hawaiian Electric Company',
      'BAE Systems P&S',
      'Island X Hawaii',
      'HawaiiUSA Federal Credit Union Foundation',
      'Oakley, Inc.',
      'Individual Sponsors and Families',
      'Armed Forces Communications and Electronics Association - AFCEA International',
    ]);
  });
});

describe('attemptToParseSchoolNameFromOldTeamName', () => {
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

describe('attemptToParseSponsors edge cases', () => {
  test('treats the last slash section as the school when it has no ampersand', () => {
    expect(attemptToParseSponsors('Company 1/Company 2')).toEqual([
      'Company 1',
    ]);
  });
});

describe('attemptToParseSponsors embedded ampersands', () => {
  // Wrong today: when every '&' in the final section looks embedded, the
  // fallback splits on the last '&' and returns ['Sponsor A', 'B'], chopping
  // "B&" off the school name.
  // Correct: "B&C High School" is the school, so the only sponsor is
  // 'Sponsor A'.
  test('Bug #50: keeps an embedded-ampersand school name intact', () => {
    expect(attemptToParseSponsors('Sponsor A/B&C High School')).toEqual([
      'Sponsor A',
    ]);
  });
});

describe('sortTeams', () => {
  test('orders teams by team number', () => {
    const teams = [{ team_number: 1678 }, { team_number: 254 }] as Team[];

    expect(sortTeams(teams).map((team) => team.team_number)).toEqual([
      254, 1678,
    ]);
  });

  test('the comparator sorts a lower team number first', () => {
    expect(
      sortTeamsComparator(
        { team_number: 254 } as Team,
        { team_number: 1678 } as Team,
      ),
    ).toBeLessThan(0);
  });
});

describe('sortTeamKeysComparator', () => {
  test('orders team keys numerically rather than lexically', () => {
    expect(['frc1678', 'frc254', 'frc33'].sort(sortTeamKeysComparator)).toEqual(
      ['frc33', 'frc254', 'frc1678'],
    );
  });
});
