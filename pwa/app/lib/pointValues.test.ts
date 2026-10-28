import { describe, expect, test } from 'vitest';

import {
  AUTO_CONTAINER_SET_2015_POINTS,
  AUTO_ROBOT_SET_2015_POINTS,
  AUTO_STACKED_TOTE_SET_2015_POINTS,
  AUTO_TOTE_SET_2015_POINTS,
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
