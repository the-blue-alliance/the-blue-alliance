import { describe, expect, test } from 'vitest';

import {
  AUTO_CONTAINER_SET_2015_POINTS,
  AUTO_MOBILITY_2018_POINTS,
  AUTO_ROBOT_SET_2015_POINTS,
  AUTO_STACKED_TOTE_SET_2015_POINTS,
  AUTO_TOTE_SET_2015_POINTS,
  ENDGAME_2018_POINTS,
} from '~/lib/pointValues';

describe('2015 autonomous sets', () => {
  test('score 4, 6, 8 and 20 for robot, tote, container and stacked tote sets', () => {
    expect([
      AUTO_ROBOT_SET_2015_POINTS,
      AUTO_TOTE_SET_2015_POINTS,
      AUTO_CONTAINER_SET_2015_POINTS,
      AUTO_STACKED_TOTE_SET_2015_POINTS,
    ]).toEqual([4, 6, 8, 20]);
  });
});

describe('2018 robot points', () => {
  test('an auto run is worth 5 and staying put nothing', () => {
    expect(AUTO_MOBILITY_2018_POINTS).toEqual({ AutoRun: 5, None: 0 });
  });

  test('climbing or levitating is worth 30 and parking 5', () => {
    expect(ENDGAME_2018_POINTS).toMatchObject({
      Climbing: 30,
      Levitate: 30,
      Parking: 5,
    });
  });
});
