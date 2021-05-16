"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const chats_1 = __importDefault(require("../chats"));
const ActionTypes_1 = require("../../constants/ActionTypes");
describe("chats reducer", () => {
  const defaultState = {
    chats: {
      firstupdatesnow: {
        name: "FIRST Updates Now",
        channel: "firstupdatesnow",
      },
    },
    renderedChats: ["firstupdatesnow"],
    currentChat: "firstupdatesnow",
    defaultChat: "firstupdatesnow",
  };
  it("defaults to the appropriate state", () => {
    expect(chats_1.default(undefined, {})).toEqual(defaultState);
  });
  it("sets the current chat", () => {
    const initialState = {
      chats: {
        chat1: {
          name: "Chat 1",
          channel: "chat1",
        },
        chat2: {
          name: "Chat 2",
          channel: "chat2",
        },
      },
      renderedChats: ["chat1"],
      currentChat: "chat1",
    };
    const expectedState = Object.assign({}, initialState, {
      renderedChats: ["chat1", "chat2"],
      currentChat: "chat2",
    });
    const action = {
      type: ActionTypes_1.SET_TWITCH_CHAT,
      channel: "chat2",
    };
    // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ chats: { chat1: { name: string... Remove this comment to see the full error message
    expect(chats_1.default(initialState, action)).toEqual(expectedState);
  });
  it("does not render an already-rendered chat again", () => {
    const initialState = {
      chats: {
        chat1: {
          name: "Chat 1",
          channel: "chat1",
        },
        chat2: {
          name: "Chat 2",
          channel: "chat2",
        },
      },
      renderedChats: ["chat1", "chat2"],
      currentChat: "chat1",
    };
    const expectedState = Object.assign({}, initialState, {
      renderedChats: ["chat1", "chat2"],
      currentChat: "chat2",
    });
    const action = {
      type: ActionTypes_1.SET_TWITCH_CHAT,
      channel: "chat2",
    };
    // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ chats: { chat1: { name: string... Remove this comment to see the full error message
    expect(chats_1.default(initialState, action)).toEqual(expectedState);
  });
});
