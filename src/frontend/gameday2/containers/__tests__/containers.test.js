import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { Provider } from "react-redux";
import * as types from "../../constants/ActionTypes";

const mockProps = {};
const mockComponent = (name) => (props) => {
  mockProps[name] = props;
  return null;
};
jest.mock("../../components/AppBar", () => mockComponent("AppBar"));
jest.mock("../../components/ChatSidebar", () => mockComponent("ChatSidebar"));
jest.mock("../../components/HashtagSidebar", () =>
  mockComponent("HashtagSidebar")
);
jest.mock("../../components/LivescoreDisplay", () =>
  mockComponent("LivescoreDisplay")
);
jest.mock("../../components/MainContent", () => mockComponent("MainContent"));
jest.mock("../../components/SwapPositionDialog", () =>
  mockComponent("SwapPositionDialog")
);
jest.mock("../../components/VideoCell", () => mockComponent("VideoCell"));
jest.mock("../../components/VideoCellToolbar", () =>
  mockComponent("VideoCellToolbar")
);
jest.mock("../../components/WebcastSelectionDialog", () =>
  mockComponent("WebcastSelectionDialog")
);

const AppBarContainer = require("../AppBarContainer").default;
const ChatSidebarContainer = require("../ChatSidebarContainer").default;
const HashtagSidebarContainer = require("../HashtagSidebarContainer").default;
const LivescoreDisplayContainer =
  require("../LivescoreDisplayContainer").default;
const MainContentContainer = require("../MainContentContainer").default;
const SwapPositionDialogContainer =
  require("../SwapPositionDialogContainer").default;
const VideoCellContainer = require("../VideoCellContainer").default;
const VideoCellToolbarContainer =
  require("../VideoCellToolbarContainer").default;
const WebcastSelectionDialogContainer =
  require("../WebcastSelectionDialogContainer").default;

const webcast = {
  key: "2024casj",
  num: 0,
  id: "2024casj-0",
  name: "SVR",
  type: "twitch",
  channel: "svr",
};

const state = {
  firedux: {
    data: {
      e: { "2024casj": { m: { qm1: { c: "qm", s: 1, m: 1, r: -1, b: -1 } } } },
      le: { "2024casj": { mk: "qm1" } },
    },
  },
  webcastsById: { "2024casj-0": webcast },
  specialWebcastIds: new Set(),
  visibility: {
    hashtagSidebar: true,
    chatSidebar: false,
    chatSidebarHasBeenVisible: true,
    layoutDrawer: true,
  },
  videoGrid: {
    layoutId: 3,
    layoutSet: true,
    displayed: ["2024casj-0"],
  },
  chats: {
    chats: { svr: { name: "SVR", channel: "svr" } },
    renderedChats: ["svr"],
    currentChat: "svr",
    defaultChat: "svr",
  },
  favoriteTeams: [{ model_key: "frc254" }],
};

let dispatch;
const renderWithStore = (element) => {
  dispatch = jest.fn();
  const store = {
    getState: () => state,
    subscribe: () => () => {},
    dispatch,
  };
  renderToStaticMarkup(<Provider store={store}>{element}</Provider>);
};

describe("gameday containers", () => {
  it("AppBarContainer maps state and dispatchers", () => {
    renderWithStore(<AppBarContainer />);
    const props = mockProps.AppBar;
    expect(props).toMatchObject({
      webcasts: ["2024casj-0"],
      layoutId: 3,
      layoutSet: true,
      hashtagSidebarVisible: true,
      chatSidebarVisible: false,
      layoutDrawerVisible: true,
    });
    props.toggleChatSidebarVisibility();
    props.setChatSidebarVisibility(true);
    props.toggleHashtagSidebarVisibility();
    props.setHashtagSidebarVisibility(false);
    props.resetWebcasts();
    props.setLayout(2);
    props.toggleLayoutDrawerVisibility();
    props.setLayoutDrawerVisibility(true);
    expect(dispatch.mock.calls.map(([action]) => action)).toEqual([
      { type: types.TOGGLE_CHAT_SIDEBAR_VISIBILITY },
      { type: types.SET_CHAT_SIDEBAR_VISIBILITY, visible: true },
      { type: types.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY },
      { type: types.SET_HASHTAG_SIDEBAR_VISIBILITY, visible: false },
      { type: types.RESET_WEBCASTS },
      { type: types.SET_LAYOUT, layoutId: 2 },
      { type: types.TOGGLE_LAYOUT_DRAWER_VISIBILITY },
      { type: types.SET_LAYOUT_DRAWER_VISIBILITY, visible: true },
    ]);
  });

  it("ChatSidebarContainer maps state and dispatchers", () => {
    renderWithStore(<ChatSidebarContainer />);
    const props = mockProps.ChatSidebar;
    expect(props).toMatchObject({
      enabled: false,
      hasBeenVisible: true,
      chats: state.chats.chats,
      displayOrderChats: [{ name: "SVR", channel: "svr" }],
      renderedChats: ["svr"],
      currentChat: "svr",
      defaultChat: "svr",
    });
    props.setTwitchChat("svr");
    props.setChatSidebarVisibility(false);
    props.setHashtagSidebarVisibility(true);
    expect(dispatch.mock.calls.map(([action]) => action)).toEqual([
      { type: types.SET_TWITCH_CHAT, channel: "svr" },
      { type: types.SET_CHAT_SIDEBAR_VISIBILITY, visible: false },
      { type: types.SET_HASHTAG_SIDEBAR_VISIBILITY, visible: true },
    ]);
  });

  it("HashtagSidebarContainer maps visibility", () => {
    renderWithStore(<HashtagSidebarContainer />);
    expect(mockProps.HashtagSidebar.enabled).toBe(true);
  });

  it("LivescoreDisplayContainer maps matches and match state for the webcast", () => {
    renderWithStore(<LivescoreDisplayContainer webcast={webcast} />);
    expect(mockProps.LivescoreDisplay.matches.map((m) => m.key)).toEqual([
      "2024casj_qm1",
    ]);
    expect(mockProps.LivescoreDisplay.matchState).toEqual({ mk: "qm1" });
  });

  it("MainContentContainer maps state and setLayout", () => {
    renderWithStore(<MainContentContainer />);
    const props = mockProps.MainContent;
    expect(props).toMatchObject({
      webcasts: ["2024casj-0"],
      hashtagSidebarVisible: true,
      chatSidebarVisible: false,
      layoutSet: true,
    });
    props.setLayout(1);
    expect(dispatch).toHaveBeenCalledWith({
      type: types.SET_LAYOUT,
      layoutId: 1,
    });
  });

  it("SwapPositionDialogContainer maps layout and swapWebcasts", () => {
    renderWithStore(<SwapPositionDialogContainer />);
    const props = mockProps.SwapPositionDialog;
    expect(props.layoutId).toBe(3);
    props.swapWebcasts(0, 1);
    expect(dispatch).toHaveBeenCalledWith({
      type: types.SWAP_WEBCASTS,
      firstPosition: 0,
      secondPosition: 1,
    });
  });

  it("VideoCellContainer maps state and dispatchers", () => {
    renderWithStore(<VideoCellContainer />);
    const props = mockProps.VideoCell;
    expect(props).toMatchObject({
      webcasts: ["2024casj-0"],
      displayedWebcasts: ["2024casj-0"],
      layoutId: 3,
    });
    props.addWebcastAtPosition("2024casj-0", 1);
    props.setLayout(4);
    props.swapWebcasts(1, 2);
    props.togglePositionLivescore(1);
    const actions = dispatch.mock.calls.map(([action]) => action);
    expect(typeof actions[0]).toBe("function");
    expect(actions.slice(1)).toEqual([
      { type: types.SET_LAYOUT, layoutId: 4 },
      { type: types.SWAP_WEBCASTS, firstPosition: 1, secondPosition: 2 },
      { type: types.TOGGLE_POSITION_LIVESCORE, position: 1 },
    ]);
  });

  it("VideoCellToolbarContainer maps state and dispatchers", () => {
    renderWithStore(<VideoCellToolbarContainer webcast={webcast} />);
    const props = mockProps.VideoCellToolbar;
    expect(props).toMatchObject({
      favoriteTeams: state.favoriteTeams,
      webcasts: ["2024casj-0"],
      webcastsById: state.webcastsById,
      specialWebcastIds: state.specialWebcastIds,
      displayedWebcasts: ["2024casj-0"],
      layoutId: 3,
    });
    expect(props.matches.map((m) => m.key)).toEqual(["2024casj_qm1"]);
    props.removeWebcast("2024casj-0");
    props.addWebcastAtPosition("2024casj-0", 0);
    props.swapWebcasts(0, 1);
    const actions = dispatch.mock.calls.map(([action]) => action);
    expect(actions[0]).toEqual({
      type: types.REMOVE_WEBCAST,
      webcastId: "2024casj-0",
    });
    expect(typeof actions[1]).toBe("function");
    expect(actions[2]).toEqual({
      type: types.SWAP_WEBCASTS,
      firstPosition: 0,
      secondPosition: 1,
    });
  });

  it("WebcastSelectionDialogContainer maps state", () => {
    renderWithStore(<WebcastSelectionDialogContainer />);
    expect(mockProps.WebcastSelectionDialog).toMatchObject({
      webcasts: ["2024casj-0"],
      webcastsById: state.webcastsById,
      specialWebcastIds: state.specialWebcastIds,
      displayedWebcasts: ["2024casj-0"],
      layoutId: 3,
    });
  });
});
