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
exports.togglePositionLivescore =
  exports.setFavoriteTeams =
  exports.setDefaultTwitchChat =
  exports.setTwitchChat =
  exports.setLayout =
  exports.resetWebcasts =
  exports.removeWebcast =
  exports.swapWebcasts =
  exports.addWebcastAtPosition =
  exports.addWebcast =
  exports.setLayoutDrawerVisibility =
  exports.toggleLayoutDrawerVisibility =
  exports.setHashtagSidebarVisibility =
  exports.toggleHashtagSidebarVisibility =
  exports.setChatSidebarVisibility =
  exports.toggleChatSidebarVisibility =
  exports.setWebcastsRaw =
    void 0;
const types = __importStar(require("../constants/ActionTypes"));
/**
 * Takes the JSON object from the server and produces a list of normalized
 * webcasts.
 */
function setWebcastsRaw(webcasts) {
  return (dispatch, getState) => {
    dispatch({
      type: types.SET_WEBCASTS_RAW,
      webcasts,
    });
    dispatch({
      type: types.WEBCASTS_UPDATED,
      webcasts: Object.assign({}, getState().webcastsById),
    });
  };
}
exports.setWebcastsRaw = setWebcastsRaw;
function toggleChatSidebarVisibility() {
  return {
    type: types.TOGGLE_CHAT_SIDEBAR_VISIBILITY,
  };
}
exports.toggleChatSidebarVisibility = toggleChatSidebarVisibility;
function setChatSidebarVisibility(visible) {
  return {
    type: types.SET_CHAT_SIDEBAR_VISIBILITY,
    visible,
  };
}
exports.setChatSidebarVisibility = setChatSidebarVisibility;
function toggleHashtagSidebarVisibility() {
  return {
    type: types.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY,
  };
}
exports.toggleHashtagSidebarVisibility = toggleHashtagSidebarVisibility;
function setHashtagSidebarVisibility(visible) {
  return {
    type: types.SET_HASHTAG_SIDEBAR_VISIBILITY,
    visible,
  };
}
exports.setHashtagSidebarVisibility = setHashtagSidebarVisibility;
function toggleLayoutDrawerVisibility() {
  return {
    type: types.TOGGLE_LAYOUT_DRAWER_VISIBILITY,
  };
}
exports.toggleLayoutDrawerVisibility = toggleLayoutDrawerVisibility;
function setLayoutDrawerVisibility(visible) {
  return {
    type: types.SET_LAYOUT_DRAWER_VISIBILITY,
    visible,
  };
}
exports.setLayoutDrawerVisibility = setLayoutDrawerVisibility;
const addWebcastNoCheck = (webcastId) => ({
  type: types.ADD_WEBCAST,
  webcastId,
});
function addWebcast(webcastId) {
  // Before displaying the webcast, check that the provided webcast ID
  // references a webcast that actually exists
  return (dispatch, getState) => {
    if (!getState().webcastsById[webcastId]) {
      return;
    }
    dispatch(addWebcastNoCheck(webcastId));
  };
}
exports.addWebcast = addWebcast;
// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'webcastId' implicitly has an 'any' type... Remove this comment to see the full error message
const addWebcastAtPositionNoCheck = (webcastId, position) => ({
  type: types.ADD_WEBCAST_AT_POSITION,
  webcastId,
  position,
});
function addWebcastAtPosition(webcastId, position) {
  // Before displaying the webcast, check that the provided webcast ID
  // references a webcast that actually exists
  return (dispatch, getState) => {
    if (!getState().webcastsById[webcastId]) {
      return;
    }
    dispatch(addWebcastAtPositionNoCheck(webcastId, position));
  };
}
exports.addWebcastAtPosition = addWebcastAtPosition;
function swapWebcasts(firstPosition, secondPosition) {
  return {
    type: types.SWAP_WEBCASTS,
    firstPosition,
    secondPosition,
  };
}
exports.swapWebcasts = swapWebcasts;
function removeWebcast(webcastId) {
  return {
    type: types.REMOVE_WEBCAST,
    webcastId,
  };
}
exports.removeWebcast = removeWebcast;
function resetWebcasts() {
  return {
    type: types.RESET_WEBCASTS,
  };
}
exports.resetWebcasts = resetWebcasts;
function setLayout(layoutId) {
  return {
    type: types.SET_LAYOUT,
    layoutId,
  };
}
exports.setLayout = setLayout;
function setTwitchChat(channel) {
  return {
    type: types.SET_TWITCH_CHAT,
    channel,
  };
}
exports.setTwitchChat = setTwitchChat;
function setDefaultTwitchChat(channel) {
  return {
    type: types.SET_DEFAULT_TWITCH_CHAT,
    channel,
  };
}
exports.setDefaultTwitchChat = setDefaultTwitchChat;
function setFavoriteTeams(favoriteTeams) {
  return {
    type: types.SET_FAVORITE_TEAMS,
    favoriteTeams,
  };
}
exports.setFavoriteTeams = setFavoriteTeams;
function togglePositionLivescore(position) {
  return {
    type: types.TOGGLE_POSITION_LIVESCORE,
    position,
  };
}
exports.togglePositionLivescore = togglePositionLivescore;
