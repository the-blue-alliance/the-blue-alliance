"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
/* eslint-disable max-len */
const ActionTypes_1 = require("../constants/ActionTypes");
/* eslint-enable max-len */
const defaultState = {
  hashtagSidebar: false,
  chatSidebar: true,
  chatSidebarHasBeenVisible: true,
  tickerSidebar: false,
  layoutDrawer: false,
};
const toggleChatSidebarVisibility = (state) => {
  const hasBeenVisible = state.chatSidebarHasBeenVisible || !state.chatSidebar;
  return Object.assign({}, state, {
    chatSidebar: !state.chatSidebar,
    chatSidebarHasBeenVisible: hasBeenVisible,
  });
};
const setChatSidebarVisibility = (visibility, state) =>
  Object.assign({}, state, {
    chatSidebar: visibility,
    chatSidebarHasBeenVisible: state.chatSidebarHasBeenVisible || visibility,
  });
const toggleHashtagSidebarVisibility = (state) =>
  Object.assign({}, state, {
    hashtagSidebar: !state.hashtagSidebar,
  });
const setHashtagSidebarVisibility = (visibility, state) =>
  Object.assign({}, state, {
    hashtagSidebar: visibility,
  });
const toggleLayoutDrawerVisibility = (state) =>
  Object.assign({}, state, {
    layoutDrawer: !state.layoutDrawer,
  });
const setLayoutDrawerVisibility = (visibility, state) =>
  Object.assign({}, state, {
    layoutDrawer: !state.layoutDrawer,
  });
const visibility = (state = defaultState, action) => {
  switch (action.type) {
    case ActionTypes_1.TOGGLE_CHAT_SIDEBAR_VISIBILITY:
      return toggleChatSidebarVisibility(state);
    case ActionTypes_1.SET_CHAT_SIDEBAR_VISIBILITY:
      return setChatSidebarVisibility(action.visible, state);
    case ActionTypes_1.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY:
      return toggleHashtagSidebarVisibility(state);
    case ActionTypes_1.SET_HASHTAG_SIDEBAR_VISIBILITY:
      return setHashtagSidebarVisibility(action.visible, state);
    case ActionTypes_1.TOGGLE_LAYOUT_DRAWER_VISIBILITY:
      return toggleLayoutDrawerVisibility(state);
    case ActionTypes_1.SET_LAYOUT_DRAWER_VISIBILITY:
      return setLayoutDrawerVisibility(action.visible, state);
    default:
      return state;
  }
};
exports.default = visibility;
