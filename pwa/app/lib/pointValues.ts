import { AutoRobot2018, EndgameRobot2018 } from '~/api/tba/read';

export const POINTS_PER_FOUL: Record<number, number> = {
  2015: 6,
  2016: 5,
  2017: 5,
  2018: 5,
  2019: 3,
  2020: 3,
  2021: 3,
  2022: 4,
  2023: 5,
  2024: 2,
  2025: 2,
};

export const POINTS_PER_TECH_FOUL: Record<number, number> = {
  2015: 6,
  2016: 5,
  2017: 25,
  2018: 25,
  2019: 10,
  2020: 15,
  2021: 15,
  2022: 8,
  2023: 12,
  2024: 5,
  2025: 6,
};

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
