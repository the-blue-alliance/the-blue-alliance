// https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/src/backend/common/consts/playoff_type.py
export enum PlayoffType {
  // Standard Brackets
  BRACKET_16_TEAM = 1,
  BRACKET_8_TEAM = 0,
  BRACKET_4_TEAM = 2,
  BRACKET_2_TEAM = 9,

  // 2015 is special
  AVG_SCORE_8_TEAM = 3,

  // Round Robin
  ROUND_ROBIN_6_TEAM = 4,

  // Double Elimination Bracket
  // The legacy style is just a basic internet bracket
  // https://www.printyourbrackets.com/fillable-brackets/8-seeded-double-fillable.pdf
  LEGACY_DOUBLE_ELIM_8_TEAM = 5,
  // The "regular" style is the one that FIRST plans to trial for the 2023 season
  // https://www.firstinspires.org/robotics/frc/blog/2022-timeout-and-playoff-tournament-updates
  DOUBLE_ELIM_8_TEAM = 10,
  // The bracket used for districts with four divisions
  DOUBLE_ELIM_4_TEAM = 11,

  // Festival of Champions
  BO5_FINALS = 6,
  BO3_FINALS = 7,

  // Custom
  CUSTOM = 8,
}

export const DOUBLE_ELIM_ROUND_MAPPING = new Map<number, number>([
  [1, 1],
  [2, 1],
  [3, 1],
  [4, 1],
  [5, 2],
  [6, 2],
  [7, 2],
  [8, 2],
  [9, 3],
  [10, 3],
  [11, 4],
  [12, 4],
  [13, 5],
]);
