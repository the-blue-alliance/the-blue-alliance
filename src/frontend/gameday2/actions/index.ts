import * as types from "../constants/ActionTypes";

/**
 * Takes the JSON object from the server and produces a list of normalized
 * webcasts.
 */
export function setWebcastsRaw(webcasts: any) {
  return (dispatch: any, getState: any) => {
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

export function toggleChatSidebarVisibility() {
  return {
    type: types.TOGGLE_CHAT_SIDEBAR_VISIBILITY,
  };
}

export function setChatSidebarVisibility(visible: any) {
  return {
    type: types.SET_CHAT_SIDEBAR_VISIBILITY,
    visible,
  };
}

export function toggleHashtagSidebarVisibility() {
  return {
    type: types.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY,
  };
}

export function setHashtagSidebarVisibility(visible: any) {
  return {
    type: types.SET_HASHTAG_SIDEBAR_VISIBILITY,
    visible,
  };
}

export function toggleLayoutDrawerVisibility() {
  return {
    type: types.TOGGLE_LAYOUT_DRAWER_VISIBILITY,
  };
}

export function setLayoutDrawerVisibility(visible: any) {
  return {
    type: types.SET_LAYOUT_DRAWER_VISIBILITY,
    visible,
  };
}

const addWebcastNoCheck = (webcastId: any) => ({
  type: types.ADD_WEBCAST,
  webcastId,
});

export function addWebcast(webcastId: any) {
  // Before displaying the webcast, check that the provided webcast ID
  // references a webcast that actually exists
  return (dispatch: any, getState: any) => {
    if (!getState().webcastsById[webcastId]) {
      return;
    }

    dispatch(addWebcastNoCheck(webcastId));
  };
}

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'webcastId' implicitly has an 'any' type... Remove this comment to see the full error message
const addWebcastAtPositionNoCheck = (webcastId, position) => ({
  type: types.ADD_WEBCAST_AT_POSITION,
  webcastId,
  position,
});

export function addWebcastAtPosition(webcastId: any, position: any) {
  // Before displaying the webcast, check that the provided webcast ID
  // references a webcast that actually exists
  return (dispatch: any, getState: any) => {
    if (!getState().webcastsById[webcastId]) {
      return;
    }

    dispatch(addWebcastAtPositionNoCheck(webcastId, position));
  };
}

export function swapWebcasts(firstPosition: any, secondPosition: any) {
  return {
    type: types.SWAP_WEBCASTS,
    firstPosition,
    secondPosition,
  };
}

export function removeWebcast(webcastId: any) {
  return {
    type: types.REMOVE_WEBCAST,
    webcastId,
  };
}

export function resetWebcasts() {
  return {
    type: types.RESET_WEBCASTS,
  };
}

export function setLayout(layoutId: any) {
  return {
    type: types.SET_LAYOUT,
    layoutId,
  };
}

export function setTwitchChat(channel: any) {
  return {
    type: types.SET_TWITCH_CHAT,
    channel,
  };
}

export function setDefaultTwitchChat(channel: any) {
  return {
    type: types.SET_DEFAULT_TWITCH_CHAT,
    channel,
  };
}

export function setFavoriteTeams(favoriteTeams: any) {
  return {
    type: types.SET_FAVORITE_TEAMS,
    favoriteTeams,
  };
}

export function togglePositionLivescore(position: any) {
  return {
    type: types.TOGGLE_POSITION_LIVESCORE,
    position,
  };
}
