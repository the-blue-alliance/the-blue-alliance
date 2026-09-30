import chats from "../chats";
import { SET_TWITCH_CHAT } from "../../constants/ActionTypes";

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
    expect(chats(undefined, {})).toEqual(defaultState);
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
      type: SET_TWITCH_CHAT,
      channel: "chat2",
    };

    expect(chats(initialState, action)).toEqual(expectedState);
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
      type: SET_TWITCH_CHAT,
      channel: "chat2",
    };

    expect(chats(initialState, action)).toEqual(expectedState);
  });
});

describe("chats reducer webcast and default chat handling", () => {
  // Load a fresh copy of the reducer for each test because WEBCASTS_UPDATED
  // mutates the module-level default state (Bug #44).
  let freshChats;
  let types;
  beforeEach(() => {
    jest.isolateModules(() => {
      freshChats = require("../chats").default;
      types = require("../../constants/ActionTypes");
    });
  });

  const webcasts = {
    bluezone: {
      key: "bluezone",
      type: "twitch",
      channel: "bluezonechannel",
      name: "BlueZone",
    },
    "2024casj-0": {
      key: "2024casj",
      type: "twitch",
      channel: "silicon_valley",
      name: "SVR",
    },
    "2024nyny-0": {
      key: "2024nyny",
      type: "youtube",
      channel: "abc123",
      name: "NYC",
    },
  };

  it("builds chats from twitch webcasts, skipping BlueZone and non-twitch webcasts", () => {
    const initial = Object.assign({}, freshChats(undefined, {}), {
      currentChat: "somechat",
      renderedChats: ["firstupdatesnow", "somechat"],
    });
    const state = freshChats(initial, {
      type: types.WEBCASTS_UPDATED,
      webcasts,
    });
    expect(state.chats).toEqual({
      firstupdatesnow: {
        name: "FIRST Updates Now",
        channel: "firstupdatesnow",
      },
      silicon_valley: { name: "SVR", channel: "silicon_valley" },
    });
    expect(state.currentChat).toBe("somechat");
    expect(state.renderedChats).toEqual(["firstupdatesnow", "somechat"]);
  });

  it("Bug #44: does not leak chats from WEBCASTS_UPDATED into the default state", () => {
    // Wrong today: setChatsFromWebcasts shallow-copies the module-level
    // default state, so twitch chats (e.g. silicon_valley) are written into
    // the shared default `chats` object and leak into the initial state.
    // Correct: the default state is unchanged by any action.
    const pristine = JSON.parse(JSON.stringify(freshChats(undefined, {})));
    freshChats(undefined, { type: types.WEBCASTS_UPDATED, webcasts });
    expect(freshChats(undefined, {})).toEqual(pristine);
  });

  it("sets the default chat to a known channel", () => {
    let state = freshChats(undefined, {
      type: types.WEBCASTS_UPDATED,
      webcasts,
    });
    state = freshChats(state, {
      type: types.SET_DEFAULT_TWITCH_CHAT,
      channel: "silicon_valley",
    });
    expect(state.defaultChat).toBe("silicon_valley");
  });

  it("ignores SET_TWITCH_CHAT for an unknown channel", () => {
    const state = freshChats(undefined, {});
    expect(
      freshChats(state, { type: types.SET_TWITCH_CHAT, channel: "nope" })
    ).toBe(state);
  });

  it("ignores SET_DEFAULT_TWITCH_CHAT for an unknown channel", () => {
    const state = freshChats(undefined, {});
    expect(
      freshChats(state, {
        type: types.SET_DEFAULT_TWITCH_CHAT,
        channel: "nope",
      })
    ).toBe(state);
  });
});
