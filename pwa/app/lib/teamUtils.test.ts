import { describe, expect, test } from 'vitest';

import type { Team } from '~/api/tba/read';
import {
  attemptToParseSchoolNameFromOldTeamName,
  attemptToParseSponsors,
  avatarYearForTeamPage,
  sortTeamKeysComparator,
  sortTeams,
  sortTeamsComparator,
} from '~/lib/teamUtils';

describe('avatarYearForTeamPage', () => {
  test.each([
    {
      name: 'uses the page year for 2018',
      year: 2018,
      yearsParticipated: [2015, 2018, 2024],
      expected: 2018,
    },
    {
      name: 'uses the page year after 2018',
      year: 2024,
      yearsParticipated: [2015, 2018, 2026],
      expected: 2024,
    },
    {
      name: 'uses the most recent active year before 2018',
      year: 2017,
      yearsParticipated: [2024, 2015, 2017],
      expected: 2024,
    },
    {
      name: 'uses the current season when years failed to load',
      year: 2017,
      yearsParticipated: null,
      expected: 2026,
    },
    {
      name: 'uses the current season when the team has no years',
      year: 2017,
      yearsParticipated: [],
      expected: 2026,
    },
  ])('$name', ({ year, yearsParticipated, expected }) => {
    expect(avatarYearForTeamPage(year, yearsParticipated, 2026)).toBe(expected);
  });
});

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

describe('attemptToParseSponsors with a known school name', () => {
  test.each([
    {
      name: 'school name contains a slash and nothing else',
      teamName: 'Centreville Jr/Sr High School',
      schoolName: 'Centreville Jr/Sr High School',
      expected: [],
    },
    {
      name: 'school name contains a slash after sponsors',
      teamName:
        'Gene Haas Foundation/Indiana Michigan Power Co/Toyota/Lennard Ag Company&Centreville Jr/Sr High School',
      schoolName: 'Centreville Jr/Sr High School',
      expected: [
        'Gene Haas Foundation',
        'Indiana Michigan Power Co',
        'Toyota',
        'Lennard Ag Company',
      ],
    },
    {
      name: 'school name contains a slash and the name has no ampersand',
      teamName: 'Osan Middle/High School',
      schoolName: 'Osan Middle/High School',
      expected: [],
    },
    {
      name: 'school name is N/A',
      teamName:
        'Egg Harbor Township Police Activities League/Atlantic County Institute of Technology/Sears&N/A',
      schoolName: 'N/A',
      expected: [
        'Egg Harbor Township Police Activities League',
        'Atlantic County Institute of Technology',
        'Sears',
      ],
    },
    {
      name: 'school name contains a slash and a dash',
      teamName:
        'LexisNexis and HPCC Systems/Concurrent Real-Time/FlexSeal&American Heritage School - Boca/Delray Palm Beach',
      schoolName: 'American Heritage School - Boca/Delray Palm Beach',
      expected: [
        'LexisNexis and HPCC Systems',
        'Concurrent Real-Time',
        'FlexSeal',
      ],
    },
    {
      name: 'school name contains an ampersand',
      teamName: 'Cambridge Rindge & Latin HS',
      schoolName: 'Cambridge Rindge & Latin HS',
      expected: [],
    },
    {
      name: 'school name contains an ampersand and a second word',
      teamName: 'University of Detroit Jesuit High School & Academy',
      schoolName: 'University of Detroit Jesuit High School & Academy',
      expected: [],
    },
    {
      name: 'last sponsor has a spaced ampersand before a spaced separator',
      teamName:
        'NASA/Comcast Corporation/JoVek Tool & Die Manufacturing/Atlantic Steel & Processing & John F. Kennedy High School',
      schoolName: 'John F. Kennedy High School',
      expected: [
        'NASA',
        'Comcast Corporation',
        'JoVek Tool & Die Manufacturing',
        'Atlantic Steel & Processing',
      ],
    },
    {
      name: 'last sponsor has a spaced ampersand before an unspaced separator',
      teamName:
        'Toronto District School Board/Motorola Solutions Foundation/WARP7 Parents & Supporters&WARP7',
      schoolName: 'WARP7',
      expected: [
        'Toronto District School Board',
        'Motorola Solutions Foundation',
        'WARP7 Parents & Supporters',
      ],
    },
    {
      name: 'last sponsor is PG&E',
      teamName:
        'FIRST Robotics/Gene Haas Foundation/Omron Foundation/Intuitive Foundation/PG&E Foundation&Monte Vista High School',
      schoolName: 'Monte Vista High School',
      expected: [
        'FIRST Robotics',
        'Gene Haas Foundation',
        'Omron Foundation',
        'Intuitive Foundation',
        'PG&E Foundation',
      ],
    },
    {
      name: 'last sponsor is PG&E with nothing after it',
      teamName:
        'The Purvis Family/DoD STEM/Typti Warehouse/PG&E&Arroyo Grande High School',
      schoolName: 'Arroyo Grande High School',
      expected: ['The Purvis Family', 'DoD STEM', 'Typti Warehouse', 'PG&E'],
    },
    {
      name: 'sponsor ampersand is followed by a spaced separator',
      teamName:
        'Toronto District School Board/Thorne Innovations/RBC Wealth Management-PH&N Investment Counsel & Westview Centennial Secondary School',
      schoolName: 'Westview Centennial Secondary School',
      expected: [
        'Toronto District School Board',
        'Thorne Innovations',
        'RBC Wealth Management-PH&N Investment Counsel',
      ],
    },
    {
      name: 'two schools listed in reverse order',
      teamName:
        'West Windsor-Plainsboro Regional School District/Apple/NASA/RoBART, Inc/SOLIDWORKS /Picatinny Arsenal/DoD STEM/Friends & Families of 1923&W Windsor-Plainsboro Hs-North&W Windsor-Plainsboro Hs-South',
      schoolName:
        'W Windsor-Plainsboro Hs-South & W Windsor-Plainsboro Hs-North',
      expected: [
        'West Windsor-Plainsboro Regional School District',
        'Apple',
        'NASA',
        'RoBART, Inc',
        'SOLIDWORKS',
        'Picatinny Arsenal',
        'DoD STEM',
        'Friends & Families of 1923',
      ],
    },
    {
      name: 'two schools with no sponsor slash',
      teamName:
        'School City of Hammond&School City of Hammond&Hammond Central High School&Morton Senior High School',
      schoolName: 'Hammond Central High School & Morton Senior High School',
      expected: ['School City of Hammond'],
    },
    {
      name: 'two schools with only the last one in the school name',
      teamName:
        'Haworth Inc./Russells Technical Products&Holland High School&Black River Public School',
      schoolName: 'Black River Public School',
      expected: ['Haworth Inc.', 'Russells Technical Products'],
    },
    {
      name: 'school name appears inside an earlier sponsor name',
      teamName:
        'Perpetual Technologies/Microsoft/International School PTSA&International School',
      schoolName: 'International School',
      expected: [
        'Perpetual Technologies',
        'Microsoft',
        'International School PTSA',
      ],
    },
    {
      name: 'schools listed in a different order than the name',
      teamName:
        'National Society of Black Engineers & Launching Eduational Assistance Programs Forward (LEAP Forward Inc.)',
      schoolName:
        'Launching Eduational Assistance Programs Forward (LEAP Forward Inc.) & National Society of Black Engineers',
      expected: [],
    },
    {
      name: 'Family/Community listed with another school in reverse order',
      teamName:
        'Martinrea/Patel Brothers/STG/Army National Guard&International Academy East&Family/Community',
      schoolName: 'Family/Community & International Academy East',
      expected: ['Martinrea', 'Patel Brothers', 'STG', 'Army National Guard'],
    },
    {
      name: 'Family/Community repeated four times',
      teamName:
        'LXT/Texas Instruments/T-Mobile Foundation&Family/Community&Family/Community&Family/Community&Family/Community',
      schoolName:
        'Family/Community & Family/Community & Family/Community & Family/Community',
      expected: ['LXT', 'Texas Instruments', 'T-Mobile Foundation'],
    },
    {
      name: 'Family/Community is the only school and repeated',
      teamName:
        'Family/Community & Family/Community & Family/Community & Family/Community',
      schoolName:
        'Family/Community & Family/Community & Family/Community & Family/Community',
      expected: [],
    },
    {
      name: 'Family/Community in the middle of several schools',
      teamName:
        'Mohave County/Parents & Families/Blackrock Power Systems&Kingman Middle School&Family/Community&Marvelous Micro School',
      schoolName:
        'Kingman Middle School & Marvelous Micro School & Family/Community',
      expected: [
        'Mohave County',
        'Parents & Families',
        'Blackrock Power Systems',
      ],
    },
    {
      name: 'school name lists only one of several spaced schools',
      teamName:
        'Kershaw County School District/Lugoff-Elgin High School/INVISTA & KC Robotics Team & Camden High School',
      schoolName: 'KC Robotics Team',
      expected: [
        'Kershaw County School District',
        'Lugoff-Elgin High School',
        'INVISTA',
      ],
    },
    {
      name: 'school name lists a middle school of a spaced name',
      teamName:
        'Walton County School District/DoDEA - Grant - Registration/Argosy Field Growth Inventive & Magnet Innovation Center & South Walton High School',
      schoolName: 'Magnet Innovation Center',
      expected: [
        'Walton County School District',
        'DoDEA - Grant - Registration',
        'Argosy Field Growth Inventive',
      ],
    },
  ])('$name', ({ teamName, schoolName, expected }) => {
    expect(attemptToParseSponsors(teamName, schoolName)).toEqual(expected);
  });

  test.each([
    {
      name: 'school name is null',
      teamName: 'Company 1/Company 2&Public High School',
      schoolName: null,
      expected: ['Company 1', 'Company 2'],
    },
    {
      name: 'school name is empty',
      teamName: 'Company 1/Company 2&Public High School',
      schoolName: '',
      expected: ['Company 1', 'Company 2'],
    },
    {
      name: 'school name is not found in the team name',
      teamName: 'Company 1/Company 2&Public High School',
      schoolName: 'Some Other School',
      expected: ['Company 1', 'Company 2'],
    },
    {
      name: 'school name only matches the middle of a sponsor',
      teamName: 'Company 1/Public High School Foundation&Public High School',
      schoolName: 'Public High',
      expected: ['Company 1', 'Public High School Foundation'],
    },
  ])(
    'falls back to the name alone when $name',
    ({ teamName, schoolName, expected }) => {
      expect(attemptToParseSponsors(teamName, schoolName)).toEqual(expected);
    },
  );
});

describe('attemptToParseSponsors without a school name', () => {
  test.each([
    {
      name: 'PG&E as the last sponsor',
      teamName: 'Company 1/Company 2/PG&E&Public High School',
      expected: ['Company 1', 'Company 2', 'PG&E'],
    },
    {
      name: 'AT&T as the last sponsor',
      teamName: 'Company 1/AT&T&Public High School',
      expected: ['Company 1', 'AT&T'],
    },
    {
      name: 'a short ampersand word followed by more words',
      teamName: 'Company 1/Company 2 P&S Group&Public High School',
      expected: ['Company 1', 'Company 2 P&S Group'],
    },
    {
      name: 'spaced ampersand in the last sponsor',
      teamName: 'Company 1/Parents & Supporters&Public High School',
      expected: ['Company 1', 'Parents & Supporters'],
    },
    {
      name: 'several spaced ampersands in the last sponsor',
      teamName: 'Company 1/Tool & Die & Machine&Public High School',
      expected: ['Company 1', 'Tool & Die & Machine'],
    },
    {
      name: 'Family/Community repeated at the end',
      teamName: 'Company 1/Company 2&Family/Community&Family/Community',
      expected: ['Company 1', 'Company 2'],
    },
    {
      name: 'Family/Community between two schools',
      teamName:
        'Company 1/Company 2&Public High School&Family/Community&Other High School',
      expected: ['Company 1', 'Company 2'],
    },
    {
      name: 'Family/Community only, repeated',
      teamName: 'Family/Community & Family/Community',
      expected: [],
    },
    {
      name: 'a trailing ampersand with nothing after it',
      teamName: 'Company 1/Company 2&',
      expected: ['Company 1', 'Company 2'],
    },
    {
      name: 'an empty name',
      teamName: '',
      expected: [],
    },
    {
      name: 'old spaced name with three schools',
      teamName:
        'Alcoa - Howmet Castings & Whitehall High School & Montague High School',
      expected: ['Alcoa - Howmet Castings'],
    },
    {
      name: 'old spaced name with four schools',
      teamName:
        'Amgen & La Reina High School & Thousand Oaks High School & Westlake High School',
      expected: ['Amgen'],
    },
    {
      name: 'old spaced name whose sponsor has an ampersand',
      teamName: 'Pratt & Whitney & Northside High School',
      expected: ['Pratt & Whitney'],
    },
    {
      name: 'old spaced name with a school that has no school word',
      teamName: 'Texas Instruments & Dighton Rehoboth Regional High School',
      expected: ['Texas Instruments'],
    },
    {
      name: 'old spaced name whose sponsor is a school district',
      teamName: 'Toronto District School Board & Westview Secondary',
      expected: ['Toronto District School Board'],
    },
  ])('$name', ({ teamName, expected }) => {
    expect(attemptToParseSponsors(teamName)).toEqual(expected);
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

describe('sortTeams', () => {
  test('orders teams by team number', () => {
    const teams = [{ team_number: 1678 }, { team_number: 254 }] as Team[];

    expect(sortTeams(teams).map((team) => team.team_number)).toEqual([
      254, 1678,
    ]);
  });

  test('leaves the input array in its original order', () => {
    const teams = [{ team_number: 1678 }, { team_number: 254 }] as Team[];

    sortTeams(teams);

    expect(teams.map((team) => team.team_number)).toEqual([1678, 254]);
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
