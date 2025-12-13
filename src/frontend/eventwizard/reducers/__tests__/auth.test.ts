import * as types from "../../constants/ActionTypes";
import authReducer from "../auth";
import { AuthState } from "../auth";

describe("auth reducer", () => {
  it("should return the initial state", () => {
    const expectedState: AuthState = {
      selectedEvent: "",
      manualEvent: false,
    };
    expect(authReducer(undefined, { type: "@@INIT" })).toEqual(expectedState);
  });

  it("should handle SET_EVENT", () => {
    const action = {
      type: types.SET_EVENT,
      eventKey: "2024test",
    };
    const expectedState: AuthState = {
      selectedEvent: "2024test",
      manualEvent: false,
    };
    expect(authReducer(undefined, action)).toEqual(expectedState);
  });

  it("should handle UPDATE_AUTH", () => {
    const action = {
      type: types.UPDATE_AUTH,
      authId: "test_id",
      authSecret: "test_secret",
    };
    const expectedState: AuthState = {
      selectedEvent: "",
      manualEvent: false,
      authId: "test_id",
      authSecret: "test_secret",
    };
    expect(authReducer(undefined, action)).toEqual(expectedState);
  });

  it("should handle CLEAR_AUTH", () => {
    const initialState: AuthState = {
      selectedEvent: "2024test",
      manualEvent: true,
      authId: "test_id",
      authSecret: "test_secret",
    };
    const action = {
      type: types.CLEAR_AUTH,
    };
    const expectedState: AuthState = {
      selectedEvent: "2024test",
      manualEvent: true,
      authId: "",
      authSecret: "",
    };
    expect(authReducer(initialState, action)).toEqual(expectedState);
  });

  it("sets manual event to true", () => {
    const action = {
      type: types.SET_MANUAL_EVENT,
      manualEvent: true,
    };
    const expectedState: AuthState = {
      selectedEvent: "",
      manualEvent: true,
    };
    expect(authReducer(undefined, action)).toEqual(expectedState);
  });

  it("sets manual event to false", () => {
    const initialState: AuthState = {
      selectedEvent: "2024test",
      manualEvent: true,
    };
    const action = {
      type: types.SET_MANUAL_EVENT,
      manualEvent: false,
    };
    const expectedState: AuthState = {
      selectedEvent: "2024test",
      manualEvent: false,
    };
    expect(authReducer(initialState, action)).toEqual(expectedState);
  });

  it("preserves existing state when updating event", () => {
    const initialState: AuthState = {
      selectedEvent: "2024old",
      manualEvent: true,
      authId: "test_id",
      authSecret: "test_secret",
    };
    const action = {
      type: types.SET_EVENT,
      eventKey: "2024new",
    };
    const expectedState: AuthState = {
      selectedEvent: "2024new",
      manualEvent: true,
      authId: "test_id",
      authSecret: "test_secret",
    };
    expect(authReducer(initialState, action)).toEqual(expectedState);
  });

  it("returns the current state for unknown actions", () => {
    const initialState: AuthState = {
      selectedEvent: "2024test",
      manualEvent: true,
    };
    const action = {
      type: "UNKNOWN_ACTION",
    };
    expect(authReducer(initialState, action as any)).toEqual(initialState);
  });
});
