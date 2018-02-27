import * as types from '../constants/ActionTypes'

/**
 * Takes the JSON object from the server and produces a list of normalized
 * webcasts.
 */
export function setWebcastsRaw(webcasts) {
  return (dispatch, getState) => {
    dispatch({
      type: types.SET_WEBCASTS_RAW,
      webcasts,
    })

    dispatch({
      type: types.WEBCASTS_UPDATED,
      webcasts: Object.assign({}, getState().webcastsById),
    })
  }
}

export function toggleChatSidebarVisibility() {
  return {
    type: types.TOGGLE_CHAT_SIDEBAR_VISIBILITY,
  }
}

export function setChatSidebarVisibility(visible) {
  return {
    type: types.SET_CHAT_SIDEBAR_VISIBILITY,
    visible,
  }
}

export function toggleHashtagSidebarVisibility() {
  return {
    type: types.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY,
  }
}

export function setHashtagSidebarVisibility(visible) {
  return {
    type: types.SET_HASHTAG_SIDEBAR_VISIBILITY,
    visible,
  }
}

export function toggleLayoutDrawerVisibility() {
  return {
    type: types.TOGGLE_LAYOUT_DRAWER_VISIBILITY,
  }
}

export function setLayoutDrawerVisibility(visible) {
  return {
    type: types.SET_LAYOUT_DRAWER_VISIBILITY,
    visible,
  }
}

const addWebcastNoCheck = (webcastId) => ({
  type: types.ADD_WEBCAST,
  webcastId,
})

export function addWebcast(webcastId) {
  // Before displaying the webcast, check that the provided webcast ID
  // references a webcast that actually exists
  return (dispatch, getState) => {
    if (!getState().webcastsById[webcastId]) {
      return
    }

    dispatch(addWebcastNoCheck(webcastId))
  }
}

const addWebcastAtPositionNoCheck = (webcastId, position) => ({
  type: types.ADD_WEBCAST_AT_POSITION,
  webcastId,
  position,
})

export function addWebcastAtPosition(webcastId, position) {
  // Before displaying the webcast, check that the provided webcast ID
  // references a webcast that actually exists
  return (dispatch, getState) => {
    if (!getState().webcastsById[webcastId]) {
      return
    }

    dispatch(addWebcastAtPositionNoCheck(webcastId, position))
  }
}

export function swapWebcasts(firstPosition, secondPosition) {
  return {
    type: types.SWAP_WEBCASTS,
    firstPosition,
    secondPosition,
  }
}

export function removeWebcast(webcastId) {
  return {
    type: types.REMOVE_WEBCAST,
    webcastId,
  }
}

export function resetWebcasts() {
  return {
    type: types.RESET_WEBCASTS,
  }
}

export function setLayout(layoutId) {
  return {
    type: types.SET_LAYOUT,
    layoutId,
  }
}

export function setTwitchChat(channel) {
  return {
    type: types.SET_TWITCH_CHAT,
    channel,
  }
}

export function setDefaultTwitchChat(channel) {
  return {
    type: types.SET_DEFAULT_TWITCH_CHAT,
    channel,
  }
}

export function setFavoriteTeams(favoriteTeams) {
  return {
    type: types.SET_FAVORITE_TEAMS,
    favoriteTeams,
  }
}

export function togglePositionLivescore(position) {
  return {
    type: types.TOGGLE_POSITION_LIVESCORE,
    position,
  }
}
