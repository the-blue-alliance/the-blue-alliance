import { describe, expect, test } from 'vitest';

import { AwardType, EventType } from '~/api/tba/read';
import {
  AwardCategory,
  BLUE_BANNER_AWARDS,
  INDIVIDUAL_AWARDS,
  MACHINE_AWARDS,
  NON_JUDGED_NON_TEAM_AWARDS,
  ROBOT_PERFORMANCE_AWARDS,
  SORT_ORDER,
  SUBMITTED_AWARDS,
  TEAM_ATTRIBUTE_AWARDS,
  getNormalizedName,
} from '~/lib/api/AwardType';

describe('getNormalizedName', () => {
  test.each([
    {
      name: "Chairman's before the 2023 rename",
      awardType: AwardType.CHAIRMANS,
      year: 2022,
      expected: "Chairman's Award",
    },
    {
      name: 'Impact from 2023',
      awardType: AwardType.CHAIRMANS,
      year: 2023,
      expected: 'FIRST Impact Award',
    },
    {
      name: "Chairman's without a year",
      awardType: AwardType.CHAIRMANS,
      year: undefined,
      expected: "Chairman's Award",
    },
    {
      name: "Chairman's Finalist before 2023",
      awardType: AwardType.CHAIRMANS_FINALIST,
      year: 2022,
      expected: "Chairman's Award Finalist",
    },
    {
      name: 'Impact Finalist from 2023',
      awardType: AwardType.CHAIRMANS_FINALIST,
      year: 2023,
      expected: 'FIRST Impact Award Finalist',
    },
    {
      name: 'event winner',
      awardType: AwardType.WINNER,
      year: undefined,
      expected: 'Winner',
    },
    {
      name: 'skills competition winner',
      awardType: AwardType.SKILLS_COMPETITION_WINNER,
      year: undefined,
      expected: 'Skills Competition Winner',
    },
    {
      name: 'game design challenge winner',
      awardType: AwardType.GAME_DESIGN_CHALLENGE_WINNER,
      year: undefined,
      expected: 'Game Design Challenge Winner',
    },
    {
      name: 'awards without a banner name',
      awardType: AwardType.SAFETY,
      year: undefined,
      expected: '',
    },
  ])('$name', ({ awardType, year, expected }) => {
    expect(getNormalizedName(awardType, undefined, year)).toBe(expected);
  });

  test('Woodie Flowers at the Championship is the award itself', () => {
    expect(
      getNormalizedName(AwardType.WOODIE_FLOWERS, EventType.CMP_FINALS),
    ).toBe('Woodie Flowers Award');
  });

  test('Woodie Flowers elsewhere is the finalist award', () => {
    expect(
      getNormalizedName(AwardType.WOODIE_FLOWERS, EventType.REGIONAL),
    ).toBe('Woodie Flowers Finalist Award');
  });
});

describe('award groupings', () => {
  test('blue banners are earned for winning and for the Impact award', () => {
    expect(BLUE_BANNER_AWARDS.has(AwardType.WINNER)).toBe(true);
    expect(BLUE_BANNER_AWARDS.has(AwardType.CHAIRMANS)).toBe(true);
  });

  test("Dean's List is an individual award", () => {
    expect(INDIVIDUAL_AWARDS.has(AwardType.DEANS_LIST)).toBe(true);
  });

  test('winner and wildcard are not judged team awards', () => {
    expect(NON_JUDGED_NON_TEAM_AWARDS.has(AwardType.WINNER)).toBe(true);
    expect(NON_JUDGED_NON_TEAM_AWARDS.has(AwardType.WILDCARD)).toBe(true);
  });

  test('autonomous is a machine award, not a team attribute award', () => {
    expect(MACHINE_AWARDS.has(AwardType.AUTONOMOUS)).toBe(true);
    expect(TEAM_ATTRIBUTE_AWARDS.has(AwardType.AUTONOMOUS)).toBe(false);
  });

  test('the Impact award is submitted ahead of the event', () => {
    expect(SUBMITTED_AWARDS.has(AwardType.CHAIRMANS)).toBe(true);
  });

  test('robot performance awards are the winner and finalist', () => {
    expect([...ROBOT_PERFORMANCE_AWARDS]).toEqual([
      AwardType.FINALIST,
      AwardType.WINNER,
    ]);
  });

  test('categories are numbered from machine to robot performance', () => {
    expect(AwardCategory).toEqual({
      MACHINE_AWARDS: 1,
      TEAM_ATTRIBUTE_AWARDS: 2,
      SUBMITTED_AWARDS: 3,
      ROBOT_PERFORMANCE_AWARDS: 4,
    });
  });

  test('the Impact award sorts first', () => {
    expect(SORT_ORDER[AwardType.CHAIRMANS]).toBe(0);
  });
});
