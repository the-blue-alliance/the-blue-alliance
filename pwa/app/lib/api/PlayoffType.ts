import { PlayoffType } from '~/api/tba/read';

export const TRADITIONAL_BRACKET_TYPES = new Set<PlayoffType | null>([
  null, // Legacy events without playoff_type
  PlayoffType.BRACKET_8_TEAM,
  PlayoffType.BRACKET_4_TEAM,
  PlayoffType.BRACKET_16_TEAM,
  PlayoffType.BRACKET_2_TEAM,
]);

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
