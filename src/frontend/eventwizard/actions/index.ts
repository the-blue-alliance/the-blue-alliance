import * as types from "../constants/ActionTypes";

// Action interfaces
export interface SetEventAction {
  type: typeof types.SET_EVENT;
  eventKey: string;
}

export interface ClearAuthAction {
  type: typeof types.CLEAR_AUTH;
}

export interface UpdateAuthAction {
  type: typeof types.UPDATE_AUTH;
  authId: string;
  authSecret: string;
}

export interface SetManualEventAction {
  type: typeof types.SET_MANUAL_EVENT;
  manualEvent: boolean;
}

// Union type for all actions
export type AuthAction =
  | SetEventAction
  | ClearAuthAction
  | UpdateAuthAction
  | SetManualEventAction;

// Action creators
export function setEvent(eventKey: string): SetEventAction {
  return {
    type: types.SET_EVENT,
    eventKey,
  };
}

export function clearAuth(): ClearAuthAction {
  return {
    type: types.CLEAR_AUTH,
  };
}

export function updateAuth(authId: string, authSecret: string): UpdateAuthAction {
  return {
    type: types.UPDATE_AUTH,
    authId,
    authSecret,
  };
}

export function setManualEvent(manualEvent: boolean): SetManualEventAction {
  return {
    type: types.SET_MANUAL_EVENT,
    manualEvent,
  };
}
