import {
  UPDATE_AUTH,
  CLEAR_AUTH,
  SET_EVENT,
  SET_MANUAL_EVENT,
} from "../constants/ActionTypes";
import { AuthAction } from "../actions";

export interface AuthState {
  selectedEvent: string;
  manualEvent: boolean;
  authId?: string;
  authSecret?: string;
}

const defaultState: AuthState = {
  selectedEvent: "",
  manualEvent: false,
};

const setNewAuth = (authId: string, authSecret: string, state: AuthState): AuthState => ({
  ...state,
  authId,
  authSecret,
});

const setNewEvent = (eventKey: string, state: AuthState): AuthState => ({
  ...state,
  selectedEvent: eventKey,
});

const setManualEvent = (manualEvent: boolean, state: AuthState): AuthState => ({
  ...state,
  manualEvent,
});

const auth = (state: AuthState = defaultState, action: AuthAction): AuthState => {
  switch (action.type) {
    case CLEAR_AUTH:
      return setNewAuth("", "", state);
    case UPDATE_AUTH:
      return setNewAuth(action.authId, action.authSecret, state);
    case SET_EVENT:
      return setNewEvent(action.eventKey, state);
    case SET_MANUAL_EVENT:
      return setManualEvent(action.manualEvent, state);
    default:
      return state;
  }
};

export default auth;
