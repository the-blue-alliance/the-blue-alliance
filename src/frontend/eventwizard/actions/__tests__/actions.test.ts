import * as types from "../../constants/ActionTypes";
import * as actions from "../index";

describe("eventwizard actions", () => {
  it("should create an action to set event", () => {
    const eventKey = "2024test";
    const expectedAction = {
      type: types.SET_EVENT,
      eventKey,
    };
    expect(actions.setEvent(eventKey)).toEqual(expectedAction);
  });

  it("should create an action to clear auth", () => {
    const expectedAction = {
      type: types.CLEAR_AUTH,
    };
    expect(actions.clearAuth()).toEqual(expectedAction);
  });

  it("should create an action to update auth", () => {
    const authId = "test_id";
    const authSecret = "test_secret";
    const expectedAction = {
      type: types.UPDATE_AUTH,
      authId,
      authSecret,
    };
    expect(actions.updateAuth(authId, authSecret)).toEqual(expectedAction);
  });

  it("should create an action to set manual event", () => {
    const expectedAction = {
      type: types.SET_MANUAL_EVENT,
      manualEvent: true,
    };
    expect(actions.setManualEvent(true)).toEqual(expectedAction);
  });

  it("should create an action to set manual event to false", () => {
    const expectedAction = {
      type: types.SET_MANUAL_EVENT,
      manualEvent: false,
    };
    expect(actions.setManualEvent(false)).toEqual(expectedAction);
  });
});
