import {
  BridgeState2023,
  EndgameRobot2019,
  MatchScoreBreakdown2016Alliance,
  MatchScoreBreakdown2017Alliance,
  MatchScoreBreakdown2018Alliance,
  MatchScoreBreakdown2019Alliance,
  MatchScoreBreakdown2020Alliance,
  MatchScoreBreakdown2022Alliance,
  MatchScoreBreakdown2023Alliance,
  MatchScoreBreakdown2024Alliance,
  MatchScoreBreakdown2025Alliance,
  MatchScoreBreakdown2026Alliance,
} from '~/api/tba/read';
import { MatchScoreBreakdownAlliance } from '~/lib/rankingPoints';

export type Station = 1 | 2 | 3;
export const STATIONS: Station[] = [1, 2, 3];

export const ROBOT_ACTIONS = ['leave', 'autoClimb', 'endgame'] as const;
export type RobotActionName = (typeof ROBOT_ACTIONS)[number];

export interface RobotAction {
  result: string;
  points: number;
}

export type RobotScore = Partial<Record<RobotActionName, RobotAction>>;

type PointTable<V> = Record<Extract<V, string>, number>;

type RobotActionSpec<A> = {
  [K in keyof A]-?: NonNullable<A[K]> extends string
    ? {
        field: K;
        points:
          | PointTable<NonNullable<A[K]>>
          | ((alliance: A, station: Station) => PointTable<NonNullable<A[K]>>);
      }
    : never;
}[keyof A];

type RobotScoringReader = (
  alliance: MatchScoreBreakdownAlliance,
  station: Station,
) => RobotScore;

function stringFields(alliance: MatchScoreBreakdownAlliance) {
  return new Map(
    Object.entries(alliance).filter(
      (entry): entry is [string, string] => typeof entry[1] === 'string',
    ),
  );
}

function robotScoring<A extends MatchScoreBreakdownAlliance>(
  spec: Partial<Record<RobotActionName, RobotActionSpec<A>>>,
): RobotScoringReader {
  return (alliance, station) => {
    const fields = stringFields(alliance);
    const score: RobotScore = {};

    for (const name of ROBOT_ACTIONS) {
      const action = spec[name];
      const result = action
        ? fields.get(String(action.field).replace(/1(\D*)$/, `${station}$1`))
        : undefined;
      if (action === undefined || result === undefined) {
        continue;
      }

      const points: Partial<Record<string, number>> =
        typeof action.points === 'function'
          ? action.points(alliance as A, station)
          : action.points;
      score[name] = { result, points: points[result] ?? 0 };
    }

    return score;
  };
}

const ROBOT_SCORING: Partial<Record<number, RobotScoringReader>> = {
  2016: robotScoring<MatchScoreBreakdown2016Alliance>({
    leave: {
      field: 'robot1Auto',
      points: { Crossed: 10, Reached: 2, Unknown: 0, None: 0 },
    },
  }),
  2017: robotScoring<MatchScoreBreakdown2017Alliance>({
    leave: {
      field: 'robot1Auto',
      points: { Mobility: 5, Unknown: 0, None: 0 },
    },
  }),
  2018: robotScoring<MatchScoreBreakdown2018Alliance>({
    leave: { field: 'autoRobot1', points: { AutoRun: 5, None: 0 } },
    endgame: {
      field: 'endgameRobot1',
      points: { Climbing: 30, Levitate: 30, Parking: 5, Unknown: 0, None: 0 },
    },
  }),
  2019: robotScoring<MatchScoreBreakdown2019Alliance>({
    leave: {
      field: 'habLineRobot1',
      points: (alliance, station) => ({
        CrossedHabLineInSandstorm:
          alliance[`preMatchLevelRobot${station}` as const] ===
          EndgameRobot2019.HAB_LEVEL2
            ? 6
            : 3,
        CrossedHabLineInTeleop: 0,
        Unknown: 0,
        None: 0,
      }),
    },
    endgame: {
      field: 'endgameRobot1',
      points: {
        HabLevel3: 12,
        HabLevel2: 6,
        HabLevel1: 3,
        Unknown: 0,
        None: 0,
      },
    },
  }),
  2020: robotScoring<MatchScoreBreakdown2020Alliance>({
    leave: { field: 'initLineRobot1', points: { Exited: 5, None: 0 } },
    endgame: { field: 'endgameRobot1', points: { Hang: 25, Park: 5, None: 0 } },
  }),
  2022: robotScoring<MatchScoreBreakdown2022Alliance>({
    leave: { field: 'taxiRobot1', points: { Yes: 2, No: 0 } },
    endgame: {
      field: 'endgameRobot1',
      points: { Traversal: 15, High: 10, Mid: 6, Low: 4, None: 0 },
    },
  }),
  2023: robotScoring<MatchScoreBreakdown2023Alliance>({
    leave: { field: 'mobilityRobot1', points: { Yes: 3, No: 0 } },
    autoClimb: {
      field: 'autoChargeStationRobot1',
      points: (alliance) =>
        alliance.autoBridgeState === BridgeState2023.LEVEL
          ? { Docked: 12, None: 0 }
          : { Docked: 8, None: 0 },
    },
    endgame: {
      field: 'endGameChargeStationRobot1',
      points: (alliance) =>
        alliance.endGameBridgeState === BridgeState2023.LEVEL
          ? { Docked: 10, Park: 2, Parked: 2, None: 0 }
          : { Docked: 6, Park: 2, Parked: 2, None: 0 },
    },
  }),
  2024: robotScoring<MatchScoreBreakdown2024Alliance>({
    leave: { field: 'autoLineRobot1', points: { Yes: 2, No: 0 } },
    endgame: {
      field: 'endGameRobot1',
      points: {
        StageLeft: 3,
        StageRight: 3,
        CenterStage: 3,
        Parked: 1,
        None: 0,
      },
    },
  }),
  2025: robotScoring<MatchScoreBreakdown2025Alliance>({
    leave: { field: 'autoLineRobot1', points: { Yes: 3, No: 0 } },
    endgame: {
      field: 'endGameRobot1',
      points: { DeepCage: 12, ShallowCage: 6, Parked: 2, None: 0 },
    },
  }),
  2026: robotScoring<MatchScoreBreakdown2026Alliance>({
    autoClimb: {
      field: 'autoTowerRobot1',
      points: { Level1: 15, Level2: 0, Level3: 0, None: 0 },
    },
    endgame: {
      field: 'endGameTowerRobot1',
      points: { Level3: 30, Level2: 20, Level1: 10, None: 0 },
    },
  }),
};

export function getRobotScore(
  year: number,
  alliance: MatchScoreBreakdownAlliance,
  station: Station,
): RobotScore | undefined {
  return ROBOT_SCORING[year]?.(alliance, station);
}

export function getRobotPoints(
  year: number,
  alliance: MatchScoreBreakdownAlliance,
  station: Station,
  action: RobotActionName,
): number {
  return getRobotScore(year, alliance, station)?.[action]?.points ?? 0;
}

const ROBOT_FIELD_PATTERN = /^(.*[Rr]obot)([123])(.*)$/;

export function getUnscoredRobotFields(
  alliance: MatchScoreBreakdownAlliance,
  station: Station,
): Record<string, string> {
  const result: Record<string, string> = {};
  for (const [key, value] of stringFields(alliance)) {
    const parts = ROBOT_FIELD_PATTERN.exec(key);
    if (parts?.[2] === String(station)) {
      result[parts[1] + parts[3]] = value;
    }
  }
  return result;
}
