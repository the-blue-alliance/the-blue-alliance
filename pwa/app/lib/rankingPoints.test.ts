import { describe, expect, test } from 'vitest';

import {
  type MatchScoreBreakdown,
  getBonusRankingPoints,
  isScoreBreakdown2016,
  isScoreBreakdown2017,
  isScoreBreakdown2018,
  isScoreBreakdown2019,
  isScoreBreakdown2020,
  isScoreBreakdown2022,
  isScoreBreakdown2023,
  isScoreBreakdown2024,
} from '~/lib/rankingPoints';

describe('rankingPoints', () => {
  test.each([
    [{ teleopDefensesBreached: true }, true],
    [{ teleopDefensesBreached: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2016 (%#)',
    (score_breakdown: MatchScoreBreakdown, expected) => {
      expect(isScoreBreakdown2016(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ kPaRankingPointAchieved: true }, true],
    [{ kPaRankingPointAchieved: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2017 (%#)',
    (score_breakdown: MatchScoreBreakdown, expected) => {
      expect(isScoreBreakdown2017(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ autoQuestRankingPoint: true }, true],
    [{ autoQuestRankingPoint: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2018 (%#)',
    (score_breakdown: MatchScoreBreakdown, expected) => {
      expect(isScoreBreakdown2018(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ completeRocketRankingPoint: true }, true],
    [{ completeRocketRankingPoint: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2019 (%#)',
    (score_breakdown: MatchScoreBreakdown, expected) => {
      expect(isScoreBreakdown2019(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ shieldEnergizedRankingPoint: true }, true],
    [{ shieldEnergizedRankingPoint: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2020 (%#)',
    (score_breakdown: MatchScoreBreakdown, expected) => {
      expect(isScoreBreakdown2020(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ cargoBonusRankingPoint: true }, true],
    [{ cargoBonusRankingPoint: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2022 (%#)',
    (score_breakdown: MatchScoreBreakdown, expected) => {
      expect(isScoreBreakdown2022(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ sustainabilityBonusAchieved: true }, true],
    [{ sustainabilityBonusAchieved: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2023 (%#)',
    (score_breakdown: MatchScoreBreakdown, expected) => {
      expect(isScoreBreakdown2023(score_breakdown)).toBe(expected);
    },
  );

  test.each([
    [{ melodyBonusAchieved: true }, true],
    [{ melodyBonusAchieved: false }, true],
    [{}, false],
  ])(
    'isScoreBreakdown2024 (%#)',
    (score_breakdown: MatchScoreBreakdown, expected) => {
      expect(isScoreBreakdown2024(score_breakdown)).toBe(expected);
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
  ])(`getBonusRankingPoints (%#)`, (score_breakdown, expected) => {
    expect(getBonusRankingPoints(score_breakdown)).toEqual(expected);
  });
});
