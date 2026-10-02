import { EventType } from '~/api/tba/read';

export const CMP_EVENT_TYPES = new Set<EventType>([
  EventType.CMP_DIVISION,
  EventType.CMP_FINALS,
]);

export const DISTRICT_EVENT_TYPES = new Set<EventType>([
  EventType.DISTRICT,
  EventType.DISTRICT_CMP_DIVISION,
  EventType.DISTRICT_CMP,
]);

export const SEASON_EVENT_TYPES = new Set<EventType>([
  EventType.REGIONAL,
  EventType.DISTRICT,
  EventType.DISTRICT_CMP_DIVISION,
  EventType.DISTRICT_CMP,
  EventType.CMP_DIVISION,
  EventType.CMP_FINALS,
  EventType.FOC,
  EventType.REMOTE,
]);
