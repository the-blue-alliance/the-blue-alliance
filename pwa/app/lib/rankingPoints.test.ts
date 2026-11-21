import { describe, expect, test } from 'vitest';

import {
  type MatchScoreBreakdown,
  type MatchScoreBreakdownAlliance,
  getBonusRankingPoints,
  isScoreBreakdown2015,
  isScoreBreakdown2015Alliance,
  isScoreBreakdown2016,
  isScoreBreakdown2016Alliance,
  isScoreBreakdown2017,
  isScoreBreakdown2017Alliance,
  isScoreBreakdown2018,
  isScoreBreakdown2018Alliance,
  isScoreBreakdown2019,
  isScoreBreakdown2019Alliance,
  isScoreBreakdown2020,
  isScoreBreakdown2020Alliance,
  isScoreBreakdown2022,
  isScoreBreakdown2022Alliance,
  isScoreBreakdown2023,
  isScoreBreakdown2023Alliance,
  isScoreBreakdown2024,
  isScoreBreakdown2024Alliance,
  isScoreBreakdown2025,
  isScoreBreakdown2025Alliance,
  isScoreBreakdown2026,
  isScoreBreakdown2026Alliance,
} from '~/lib/rankingPoints';

describe('rankingPoints', () => {
  test.each([
    [{ teleopDefensesBreached: true }, true],
    [{ teleopDefensesBreached: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2016Alliance (%#)',
    (score_breakdown: Partial<MatchScoreBreakdownAlliance>, expected) => {
      // @ts-expect-error - score_breakdown can be a partial for testing
      expect(isScoreBreakdown2016Alliance(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ kPaRankingPointAchieved: true }, true],
    [{ kPaRankingPointAchieved: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2017Alliance (%#)',
    (score_breakdown: Partial<MatchScoreBreakdownAlliance>, expected) => {
      // @ts-expect-error - score_breakdown can be a partial for testing
      expect(isScoreBreakdown2017Alliance(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ autoQuestRankingPoint: true }, true],
    [{ autoQuestRankingPoint: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2018Alliance (%#)',
    (score_breakdown: Partial<MatchScoreBreakdownAlliance>, expected) => {
      // @ts-expect-error - score_breakdown can be a partial for testing
      expect(isScoreBreakdown2018Alliance(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ completeRocketRankingPoint: true }, true],
    [{ completeRocketRankingPoint: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2019Alliance (%#)',
    (score_breakdown: Partial<MatchScoreBreakdownAlliance>, expected) => {
      // @ts-expect-error - score_breakdown can be a partial for testing
      expect(isScoreBreakdown2019Alliance(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ shieldEnergizedRankingPoint: true }, true],
    [{ shieldEnergizedRankingPoint: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2020Alliance (%#)',
    (score_breakdown: Partial<MatchScoreBreakdownAlliance>, expected) => {
      // @ts-expect-error - score_breakdown can be a partial for testing
      expect(isScoreBreakdown2020Alliance(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ cargoBonusRankingPoint: true }, true],
    [{ cargoBonusRankingPoint: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2022Alliance (%#)',
    (score_breakdown: Partial<MatchScoreBreakdownAlliance>, expected) => {
      // @ts-expect-error - score_breakdown can be a partial for testing
      expect(isScoreBreakdown2022Alliance(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ sustainabilityBonusAchieved: true }, true],
    [{ sustainabilityBonusAchieved: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2023Alliance (%#)',
    (score_breakdown: Partial<MatchScoreBreakdownAlliance>, expected) => {
      // @ts-expect-error - score_breakdown can be a partial for testing
      expect(isScoreBreakdown2023Alliance(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ melodyBonusAchieved: true }, true],
    [{ melodyBonusAchieved: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2024Alliance (%#)',
    (score_breakdown: Partial<MatchScoreBreakdownAlliance>, expected) => {
      // @ts-expect-error - score_breakdown can be a partial for testing
      expect(isScoreBreakdown2024Alliance(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ coralBonusAchieved: true }, true],
    [{ coralBonusAchieved: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2025Alliance (%#)',
    (score_breakdown: Partial<MatchScoreBreakdownAlliance>, expected) => {
      // @ts-expect-error - score_breakdown can be a partial for testing
      expect(isScoreBreakdown2025Alliance(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ energizedAchieved: true }, true],
    [{ energizedAchieved: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2026Alliance (%#)',
    (score_breakdown: Partial<MatchScoreBreakdownAlliance>, expected) => {
      // @ts-expect-error - score_breakdown can be a partial for testing
      expect(isScoreBreakdown2026Alliance(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ teleopDefensesBreached: true }, [true, false]],
    [
      { teleopDefensesBreached: false, teleopTowerCaptured: true },
      [false, true],
    ],
    [{ teleopDefensesBreached: true, teleopTowerCaptured: true }, [true, true]],

    // 2017
    [{ kPaRankingPointAchieved: true }, [true, false]],
    [
      { kPaRankingPointAchieved: false, rotorRankingPointAchieved: true },
      [false, true],
    ],
    [
      { kPaRankingPointAchieved: true, rotorRankingPointAchieved: true },
      [true, true],
    ],

    // 2018
    [{ autoQuestRankingPoint: true }, [true, false]],
    [
      { autoQuestRankingPoint: false, faceTheBossRankingPoint: true },
      [false, true],
    ],
    [
      { autoQuestRankingPoint: true, faceTheBossRankingPoint: true },
      [true, true],
    ],

    // 2019
    [{ completeRocketRankingPoint: true }, [true, false]],
    [
      { completeRocketRankingPoint: false, habDockingRankingPoint: true },
      [false, true],
    ],
    [
      { completeRocketRankingPoint: true, habDockingRankingPoint: true },
      [true, true],
    ],

    // 2020
    [{ shieldEnergizedRankingPoint: true }, [true, false]],
    [
      {
        shieldEnergizedRankingPoint: false,
        shieldOperationalRankingPoint: true,
      },
      [false, true],
    ],
    [
      {
        shieldEnergizedRankingPoint: true,
        shieldOperationalRankingPoint: true,
      },
      [true, true],
    ],

    // 2022
    [{ cargoBonusRankingPoint: true }, [true, false]],
    [
      { cargoBonusRankingPoint: false, hangarBonusRankingPoint: true },
      [false, true],
    ],
    [
      { cargoBonusRankingPoint: true, hangarBonusRankingPoint: true },
      [true, true],
    ],

    // 2023
    [{ sustainabilityBonusAchieved: true }, [true, false]],
    [
      { sustainabilityBonusAchieved: false, activationBonusAchieved: true },
      [false, true],
    ],
    [
      { sustainabilityBonusAchieved: true, activationBonusAchieved: true },
      [true, true],
    ],

    // 2024
    [{ melodyBonusAchieved: true }, [true, false]],
    [
      { melodyBonusAchieved: false, ensembleBonusAchieved: true },
      [false, true],
    ],
    [{ melodyBonusAchieved: true, ensembleBonusAchieved: true }, [true, true]],

    // 2025
    [{ coralBonusAchieved: true }, [false, true, false]],
    [
      { autoBonusAchieved: true, coralBonusAchieved: false },
      [true, false, false],
    ],
    [
      {
        autoBonusAchieved: true,
        coralBonusAchieved: true,
        bargeBonusAchieved: true,
      },
      [true, true, true],
    ],

    // 2026
    [{ energizedAchieved: true }, [true, false, false]],
    [
      { energizedAchieved: false, superchargedAchieved: true },
      [false, true, false],
    ],
    [
      {
        energizedAchieved: true,
        superchargedAchieved: true,
        traversalAchieved: true,
      },
      [true, true, true],
    ],
  ])(
    `getBonusRankingPoints (%#)`,
    (score_breakdown: Partial<MatchScoreBreakdownAlliance>, expected) => {
      // @ts-expect-error - score_breakdown can be a partial for testing
      expect(getBonusRankingPoints(score_breakdown)).toEqual(expected);
    },
  );
});

describe('match score breakdown guards', () => {
  const guards = [
    {
      year: 2015,
      guard: isScoreBreakdown2015,
      marker: 'container_count_level1',
    },
    {
      year: 2016,
      guard: isScoreBreakdown2016,
      marker: 'teleopDefensesBreached',
    },
    {
      year: 2017,
      guard: isScoreBreakdown2017,
      marker: 'kPaRankingPointAchieved',
    },
    {
      year: 2018,
      guard: isScoreBreakdown2018,
      marker: 'autoQuestRankingPoint',
    },
    {
      year: 2019,
      guard: isScoreBreakdown2019,
      marker: 'completeRocketRankingPoint',
    },
    {
      year: 2020,
      guard: isScoreBreakdown2020,
      marker: 'shieldEnergizedRankingPoint',
    },
    {
      year: 2022,
      guard: isScoreBreakdown2022,
      marker: 'cargoBonusRankingPoint',
    },
    {
      year: 2023,
      guard: isScoreBreakdown2023,
      marker: 'sustainabilityBonusAchieved',
    },
    { year: 2024, guard: isScoreBreakdown2024, marker: 'melodyBonusAchieved' },
    { year: 2025, guard: isScoreBreakdown2025, marker: 'coralBonusAchieved' },
    { year: 2026, guard: isScoreBreakdown2026, marker: 'energizedAchieved' },
  ];

  function breakdownWith(field: string): MatchScoreBreakdown {
    return {
      red: { [field]: 0 },
      blue: { [field]: 0 },
    } as unknown as MatchScoreBreakdown;
  }

  test.each(guards)(
    'isScoreBreakdown$year recognises a $year breakdown',
    ({ guard, marker }) => {
      expect(guard(breakdownWith(marker))).toBe(true);
    },
  );

  test.each(guards)(
    'isScoreBreakdown$year rejects a breakdown from another season',
    ({ guard }) => {
      expect(guard(breakdownWith('somethingElse'))).toBe(false);
    },
  );

  test.each(guards)(
    'isScoreBreakdown$year rejects a missing breakdown',
    ({ guard }) => {
      expect(guard(null)).toBe(false);
    },
  );

  test.each([
    [{ container_count_level1: 0 }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2015Alliance (%#)',
    (score_breakdown: Partial<MatchScoreBreakdownAlliance>, expected) => {
      // @ts-expect-error - score_breakdown can be a partial for testing
      expect(isScoreBreakdown2015Alliance(score_breakdown)).toBe(expected);
    },
  );

  test('getBonusRankingPoints has no bonus points for a 2015 alliance', () => {
    expect(getBonusRankingPoints({ container_count_level1: 0 })).toEqual([]);
  });
});
