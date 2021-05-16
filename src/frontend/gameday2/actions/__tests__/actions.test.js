"use strict";
var __createBinding =
  (this && this.__createBinding) ||
  (Object.create
    ? function (o, m, k, k2) {
        if (k2 === undefined) k2 = k;
        Object.defineProperty(o, k2, {
          enumerable: true,
          get: function () {
            return m[k];
          },
        });
      }
    : function (o, m, k, k2) {
        if (k2 === undefined) k2 = k;
        o[k2] = m[k];
      });
var __setModuleDefault =
  (this && this.__setModuleDefault) ||
  (Object.create
    ? function (o, v) {
        Object.defineProperty(o, "default", { enumerable: true, value: v });
      }
    : function (o, v) {
        o["default"] = v;
      });
var __importStar =
  (this && this.__importStar) ||
  function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null)
      for (var k in mod)
        if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k))
          __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
  };
Object.defineProperty(exports, "__esModule", { value: true });
const types = __importStar(require("../../constants/ActionTypes"));
const actions = __importStar(require("../index"));
describe("actions", () => {
  it("should create an action to set webcsts from raw data", () => {
    const getState = () => ({
      webcastsById: {},
    });
    const dispatch = jasmine.createSpy();
    const webcasts = {};
    actions.setWebcastsRaw(webcasts)(dispatch, getState);
    expect(dispatch.calls.count()).toBe(2);
    expect(dispatch.calls.argsFor(0)).toEqual([
      {
        type: types.SET_WEBCASTS_RAW,
        webcasts,
      },
    ]);
    expect(dispatch.calls.argsFor(1)).toEqual([
      {
        type: types.WEBCASTS_UPDATED,
        webcasts: {},
      },
    ]);
  });
  it("should create an action to toggle the hashtag sidebar visibility", () => {
    const expectedAction = {
      type: types.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY,
    };
    expect(actions.toggleHashtagSidebarVisibility()).toEqual(expectedAction);
  });
  it("should create an action to toggle the chat sidebar visibility", () => {
    const expectedAction = {
      type: types.TOGGLE_CHAT_SIDEBAR_VISIBILITY,
    };
    expect(actions.toggleChatSidebarVisibility()).toEqual(expectedAction);
  });
  it("should create an action to toggle the layout drawer visibility", () => {
    const expectedAction = {
      type: types.TOGGLE_LAYOUT_DRAWER_VISIBILITY,
    };
    expect(actions.toggleLayoutDrawerVisibility()).toEqual(expectedAction);
  });
  it("should create an action to add a webcast if the webcast ID exists in webcastsById", () => {
    const webcastId = "a";
    const getState = () => ({
      webcastsById: {
        [webcastId]: {},
      },
    });
    const dispatch = jasmine.createSpy();
    actions.addWebcast(webcastId)(dispatch, getState);
    expect(dispatch).toHaveBeenCalledWith({
      type: types.ADD_WEBCAST,
      webcastId,
    });
  });
  it("should not create an action to add a webcast if the webcast ID does not exist in webcastsById", () => {
    const getState = () => ({
      webcastsById: {},
    });
    const dispatch = jasmine.createSpy();
    actions.addWebcast("a")(dispatch, getState);
    expect(dispatch.calls.any()).toBe(false);
  });
  it("should create an action to add a webcast at a specific position if the webcast ID exists in webcastsById", () => {
    const webcastId = "a";
    const position = 0;
    const getState = () => ({
      webcastsById: {
        [webcastId]: {},
      },
    });
    const dispatch = jasmine.createSpy();
    actions.addWebcastAtPosition(webcastId, position)(dispatch, getState);
    expect(dispatch).toHaveBeenCalledWith({
      type: types.ADD_WEBCAST_AT_POSITION,
      webcastId,
      position,
    });
  });
  it("should not create an action to add a webcast at a specific position if the webcast ID does not exist in webcastsById", () => {
    const webcastId = "a";
    const position = 0;
    const getState = () => ({
      webcastsById: {},
    });
    const dispatch = jasmine.createSpy();
    actions.addWebcastAtPosition(webcastId, position)(dispatch, getState);
    expect(dispatch.calls.any()).toBe(false);
  });
  it("should create an action to swap two webcasts", () => {
    const firstPosition = 0;
    const secondPosition = 1;
    const expectedAction = {
      type: types.SWAP_WEBCASTS,
      firstPosition,
      secondPosition,
    };
    expect(actions.swapWebcasts(firstPosition, secondPosition)).toEqual(
      expectedAction
    );
  });
  it("should create an action to remove a specified webcast", () => {
    const webcastId = "a";
    const expectedAction = {
      type: types.REMOVE_WEBCAST,
      webcastId,
    };
    expect(actions.removeWebcast(webcastId)).toEqual(expectedAction);
  });
  it("should create an action to reset all webcasts", () => {
    const expectedAction = {
      type: types.RESET_WEBCASTS,
    };
    expect(actions.resetWebcasts()).toEqual(expectedAction);
  });
  it("should create an action to set the layout", () => {
    const layoutId = 3;
    const expectedAction = {
      type: types.SET_LAYOUT,
      layoutId,
    };
    expect(actions.setLayout(layoutId)).toEqual(expectedAction);
  });
  it("should create an action to set the current twitch chat", () => {
    const channel = "tbagameday";
    const expectedAction = {
      type: types.SET_TWITCH_CHAT,
      channel,
    };
    expect(actions.setTwitchChat(channel)).toEqual(expectedAction);
  });
});
