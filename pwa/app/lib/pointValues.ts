import { AutoRobot2018, EndgameRobot2018 } from '~/api/tba/read';

/**
 * Manual links for quick reference:
 *
 * 2015: https://firstfrc.blob.core.windows.net/frcarchive/2015/2015-game-manual.pdf
 * 2018: https://firstfrc.blob.core.windows.net/frc2018/Manual/2018FRCGameSeasonManual.pdf
 */

// 2015
export const AUTO_ROBOT_SET_2015_POINTS: number = 4;
export const AUTO_TOTE_SET_2015_POINTS: number = 6;
export const AUTO_CONTAINER_SET_2015_POINTS: number = 8;
export const AUTO_STACKED_TOTE_SET_2015_POINTS: number = 20;

// 2018
export const AUTO_MOBILITY_2018_POINTS: Record<AutoRobot2018, number> = {
  AutoRun: 5,
  None: 0,
};
export const ENDGAME_2018_POINTS: Record<EndgameRobot2018, number> = {
  Climbing: 30,
  Levitate: 30,
  Parking: 5,
  Unknown: 0,
  None: 0,
};
