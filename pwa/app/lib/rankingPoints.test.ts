import { describe, expect, test } from 'vitest';

import {
  type MatchScoreBreakdownAlliance,
  getBonusRankingPoints,
  isScoreBreakdown2016Alliance,
  isScoreBreakdown2017Alliance,
  isScoreBreakdown2018Alliance,
  isScoreBreakdown2019Alliance,
  isScoreBreakdown2020Alliance,
  isScoreBreakdown2022Alliance,
  isScoreBreakdown2023Alliance,
  isScoreBreakdown2024Alliance,
  isScoreBreakdown2025Alliance,
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
