import authReducer from "../auth";
import * as types from "../../constants/ActionTypes";

describe("auth reducer", () => {
  it("defaults to the appropriate state", () => {
    const expectedState = {
      selectedEvent: "",
      manualEvent: false,
    };
    expect(authReducer(undefined, {})).toEqual(expectedState);
  });

  it("sets the event", () => {
    const eventKey = "2024test";
    const action = {
      type: types.SET_EVENT,
      eventKey,
    };
    const expectedState = {
      selectedEvent: eventKey,
      manualEvent: false,
    };
    expect(authReducer(undefined, action)).toEqual(expectedState);
  });

  it("updates auth credentials", () => {
    const authId = "test_id";
    const authSecret = "test_secret";
    const action = {
      type: types.UPDATE_AUTH,
      authId,
      authSecret,
    };
    const expectedState = {
      selectedEvent: "",
      manualEvent: false,
      authId,
      authSecret,
    };
    expect(authReducer(undefined, action)).toEqual(expectedState);
  });

  it("clears auth credentials", () => {
    const initialState = {
      selectedEvent: "2024test",
      manualEvent: true,
      authId: "test_id",
      authSecret: "test_secret",
    };
    const action = {
      type: types.CLEAR_AUTH,
    };
    const expectedState = {
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
    const expectedState = {
      selectedEvent: "",
      manualEvent: true,
    };
    expect(authReducer(undefined, action)).toEqual(expectedState);
  });

  it("sets manual event to false", () => {
    const initialState = {
      selectedEvent: "2024test",
      manualEvent: true,
    };
    const action = {
      type: types.SET_MANUAL_EVENT,
      manualEvent: false,
    };
    const expectedState = {
      selectedEvent: "2024test",
      manualEvent: false,
    };
    expect(authReducer(initialState, action)).toEqual(expectedState);
  });

  it("preserves existing state when updating event", () => {
    const initialState = {
      selectedEvent: "2024old",
      manualEvent: true,
      authId: "test_id",
      authSecret: "test_secret",
    };
    const action = {
      type: types.SET_EVENT,
      eventKey: "2024new",
    };
    const expectedState = {
      selectedEvent: "2024new",
      manualEvent: true,
      authId: "test_id",
      authSecret: "test_secret",
    };
    expect(authReducer(initialState, action)).toEqual(expectedState);
  });

  it("returns the current state for unknown actions", () => {
    const initialState = {
      selectedEvent: "2024test",
      manualEvent: true,
    };
    const action = {
      type: "UNKNOWN_ACTION",
    };
    expect(authReducer(initialState, action)).toEqual(initialState);
  });
});
