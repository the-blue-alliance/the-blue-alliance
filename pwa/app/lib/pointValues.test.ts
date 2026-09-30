import { describe, expect, test } from 'vitest';

import {
  AUTO_CONTAINER_SET_2015_POINTS,
  AUTO_MOBILITY_2018_POINTS,
  AUTO_ROBOT_SET_2015_POINTS,
  AUTO_STACKED_TOTE_SET_2015_POINTS,
  AUTO_TOTE_SET_2015_POINTS,
  ENDGAME_2018_POINTS,
  POINTS_PER_FOUL,
  POINTS_PER_TECH_FOUL,
} from '~/lib/pointValues';

describe('foul values', () => {
  test.each([
    { year: 2015, foul: 6, techFoul: 6 },
    { year: 2018, foul: 5, techFoul: 25 },
    { year: 2025, foul: 2, techFoul: 6 },
  ])(
    '$year fouls cost $foul and tech fouls $techFoul',
    ({ year, foul, techFoul }) => {
      expect(POINTS_PER_FOUL[year]).toBe(foul);
      expect(POINTS_PER_TECH_FOUL[year]).toBe(techFoul);
    },
  );
});

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
