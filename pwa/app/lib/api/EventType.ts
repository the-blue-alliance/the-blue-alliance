// https://raw.githubusercontent.com/the-blue-alliance/the-blue-alliance/master/consts/event_type.py
export enum EventType {
  REGIONAL = 0,
  DISTRICT = 1,
  DISTRICT_CMP = 2,
  CMP_DIVISION = 3,
  CMP_FINALS = 4,
  DISTRICT_CMP_DIVISION = 5,
  FOC = 6,
  REMOTE = 7,

  OFFSEASON = 99,
  PRESEASON = 100,
  UNLABLED = -1,
}

export const CMP_EVENT_TYPES = new Set([
  EventType.CMP_DIVISION,
  EventType.CMP_FINALS,
]);

export const SEASON_EVENT_TYPES = new Set([
  EventType.REGIONAL,
  EventType.DISTRICT,
  EventType.DISTRICT_CMP_DIVISION,
  EventType.DISTRICT_CMP,
  EventType.CMP_DIVISION,
  EventType.CMP_FINALS,
  EventType.FOC,
  EventType.REMOTE,
]);
