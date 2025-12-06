export const UPDATE_AUTH = "UPDATE_AUTH" as const;
export const CLEAR_AUTH = "CLEAR_AUTH" as const;
export const SET_EVENT = "SET_EVENT" as const;
export const SET_MANUAL_EVENT = "SET_MANUAL_EVENT" as const;

export type ActionType =
  | typeof UPDATE_AUTH
  | typeof CLEAR_AUTH
  | typeof SET_EVENT
  | typeof SET_MANUAL_EVENT;
