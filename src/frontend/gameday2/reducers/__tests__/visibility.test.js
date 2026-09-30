import visibility from "../visibility";
import * as types from "../../constants/ActionTypes";

describe("visibility reducer", () => {
  const defaultState = {
    hashtagSidebar: false,
    chatSidebar: true,
    chatSidebarHasBeenVisible: true,
    tickerSidebar: false,
    layoutDrawer: false,
  };

  it("defaults all views to not visibile", () => {
    expect(visibility(undefined, {})).toEqual(defaultState);
  });

  it("toggles chat sidebar from true to false", () => {
    const initialState = defaultState;
    const expectedState = Object.assign({}, defaultState, {
      chatSidebar: false,
      chatSidebarHasBeenVisible: true,
    });
    const action = {
      type: types.TOGGLE_CHAT_SIDEBAR_VISIBILITY,
    };
    expect(visibility(initialState, action)).toEqual(expectedState);
  });

  it("toggles chat sidebar from false to true", () => {
    const initialState = Object.assign({}, defaultState, {
      chatSidebar: false,
      chatSidebarHasBeenVisible: true,
    });
    const expectedState = Object.assign({}, defaultState, {
      chatSidebar: true,
      chatSidebarHasBeenVisible: true,
    });
    const action = {
      type: types.TOGGLE_CHAT_SIDEBAR_VISIBILITY,
    };
    expect(visibility(initialState, action)).toEqual(expectedState);
  });

  it("toggles hashtag sidebar from false to true", () => {
    const initialState = defaultState;
    const expectedState = Object.assign({}, defaultState, {
      hashtagSidebar: true,
    });
    const action = {
      type: types.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY,
    };
    expect(visibility(initialState, action)).toEqual(expectedState);
  });

  it("toggles hashtag sidebar from true to false", () => {
    const initialState = Object.assign({}, defaultState, {
      hashtagSidebar: true,
    });
    const expectedState = defaultState;
    const action = {
      type: types.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY,
    };
    expect(visibility(initialState, action)).toEqual(expectedState);
  });

  it("toggles layout drawer from false to true", () => {
    const initialState = defaultState;
    const expectedState = Object.assign({}, defaultState, {
      layoutDrawer: true,
    });
    const action = {
      type: types.TOGGLE_LAYOUT_DRAWER_VISIBILITY,
    };
    expect(visibility(initialState, action)).toEqual(expectedState);
  });

  it("toggles layout drawer from true to false", () => {
    const initialState = Object.assign({}, defaultState, {
      layoutDrawer: true,
    });
    const expectedState = defaultState;
    const action = {
      type: types.TOGGLE_LAYOUT_DRAWER_VISIBILITY,
    };
    expect(visibility(initialState, action)).toEqual(expectedState);
  });
});

describe("visibility reducer set actions", () => {
  const defaultState = visibility(undefined, {});

  it("returns the same state for unknown actions", () => {
    expect(visibility(defaultState, { type: "UNKNOWN" })).toBe(defaultState);
  });

  it("sets the chat sidebar visibility and remembers it was visible", () => {
    const hidden = visibility(
      Object.assign({}, defaultState, { chatSidebarHasBeenVisible: false }),
      { type: types.SET_CHAT_SIDEBAR_VISIBILITY, visible: false }
    );
    expect(hidden.chatSidebar).toBe(false);
    expect(hidden.chatSidebarHasBeenVisible).toBe(false);

    const shown = visibility(hidden, {
      type: types.SET_CHAT_SIDEBAR_VISIBILITY,
      visible: true,
    });
    expect(shown.chatSidebar).toBe(true);
    expect(shown.chatSidebarHasBeenVisible).toBe(true);
  });

  it("sets the hashtag sidebar visibility", () => {
    expect(
      visibility(defaultState, {
        type: types.SET_HASHTAG_SIDEBAR_VISIBILITY,
        visible: true,
      }).hashtagSidebar
    ).toBe(true);
  });

  it("opens the layout drawer on SET_LAYOUT_DRAWER_VISIBILITY visible: true", () => {
    const opened = visibility(defaultState, {
      type: types.SET_LAYOUT_DRAWER_VISIBILITY,
      visible: true,
    });
    expect(opened.layoutDrawer).toBe(true);
  });
});
