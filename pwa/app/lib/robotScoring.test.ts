import { describe, expect, test } from 'vitest';

import {
  BridgeState2023,
  EndGameChargeStationRobot2023,
  EndGameRobot2024,
  EndgameRobot2019,
  HabLine2019,
  type MatchScoreBreakdown2016Alliance,
  type MatchScoreBreakdown2019Alliance,
  type MatchScoreBreakdown2023Alliance,
  type MatchScoreBreakdown2024Alliance,
  type MatchScoreBreakdown2026Alliance,
  RobotAuto2016WithUnknown,
  TowerRobot2026,
} from '~/api/tba/read';
import {
  getRobotPoints,
  getRobotScore,
  getUnscoredRobotFields,
} from '~/lib/robotScoring';

const alliance2026 = {
  autoTowerRobot1: TowerRobot2026.LEVEL1,
  autoTowerRobot2: TowerRobot2026.NONE,
  autoTowerRobot3: TowerRobot2026.NONE,
  endGameTowerRobot1: TowerRobot2026.LEVEL3,
  endGameTowerRobot2: TowerRobot2026.LEVEL2,
  endGameTowerRobot3: TowerRobot2026.NONE,
} as MatchScoreBreakdown2026Alliance;

describe('getRobotScore', () => {
  test('scores a 2026 auto Level 1 climb as 15 points', () => {
    expect(getRobotScore(2026, alliance2026, 1)?.autoClimb).toEqual({
      result: 'Level1',
      points: 15,
    });
  });

  test('scores a 2026 endgame Level 3 climb as 30 points', () => {
    expect(getRobotScore(2026, alliance2026, 1)?.endgame).toEqual({
      result: 'Level3',
      points: 30,
    });
  });

  test('reads the fields of the requested station', () => {
    expect(getRobotScore(2026, alliance2026, 2)?.endgame).toEqual({
      result: 'Level2',
      points: 20,
    });
  });

  test('has no leave action in 2026', () => {
    expect(getRobotScore(2026, alliance2026, 1)?.leave).toBeUndefined();
  });

  test('reads fields that put the station number mid-name', () => {
    const alliance = {
      robot3Auto: RobotAuto2016WithUnknown.CROSSED,
    } as MatchScoreBreakdown2016Alliance;

    expect(getRobotScore(2016, alliance, 3)?.leave).toEqual({
      result: 'Crossed',
      points: 10,
    });
  });

  test.each([
    { bridge: BridgeState2023.LEVEL, points: 10 },
    { bridge: BridgeState2023.NOT_LEVEL, points: 6 },
  ])(
    'scores a 2023 endgame dock on a $bridge station as $points',
    ({ bridge, points }) => {
      const alliance = {
        endGameChargeStationRobot1: EndGameChargeStationRobot2023.DOCKED,
        endGameBridgeState: bridge,
      } as MatchScoreBreakdown2023Alliance;

      expect(getRobotScore(2023, alliance, 1)?.endgame?.points).toBe(points);
    },
  );

  test.each([
    { start: EndgameRobot2019.HAB_LEVEL1, points: 3 },
    { start: EndgameRobot2019.HAB_LEVEL2, points: 6 },
  ])(
    'scores a 2019 sandstorm crossing from $start as $points',
    ({ start, points }) => {
      const alliance = {
        habLineRobot1: HabLine2019.CROSSED_HAB_LINE_IN_SANDSTORM,
        preMatchLevelRobot1: start,
      } as MatchScoreBreakdown2019Alliance;

      expect(getRobotScore(2019, alliance, 1)?.leave?.points).toBe(points);
    },
  );

  test('omits an action whose field is missing', () => {
    const alliance = {
      endGameRobot1: EndGameRobot2024.PARKED,
    } as MatchScoreBreakdown2024Alliance;

    expect(getRobotScore(2024, alliance, 1)?.leave).toBeUndefined();
  });

  test('returns nothing for a year without scoring', () => {
    expect(getRobotScore(2027, alliance2026, 1)).toBeUndefined();
  });
});

describe('getRobotPoints', () => {
  test('returns the points of the requested action', () => {
    expect(getRobotPoints(2026, alliance2026, 2, 'endgame')).toBe(20);
  });

  test('returns 0 for a year without scoring', () => {
    expect(getRobotPoints(2027, alliance2026, 1, 'endgame')).toBe(0);
  });
});

describe('getUnscoredRobotFields', () => {
  test('lists the station fields without the station number', () => {
    const alliance = {
      climbRobot1: 'High',
      climbRobot2: 'Low',
    } as unknown as MatchScoreBreakdown2026Alliance;

    expect(getUnscoredRobotFields(alliance, 2)).toEqual({ climbRobot: 'Low' });
  });

  test('ignores numbered fields that are not about robots', () => {
    const alliance = {
      bay1: 'Panel',
    } as unknown as MatchScoreBreakdown2026Alliance;

    expect(getUnscoredRobotFields(alliance, 1)).toEqual({});
  });
});
