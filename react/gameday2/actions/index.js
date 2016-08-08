import * as types from '../constants/ActionTypes'

/**
 * Takes the JSON object from the server and produces a list of normalized
 * webcasts.
 */
export function setWebcastsRaw(webcasts) {
  return {
    type: types.SET_WEBCASTS_RAW,
    webcasts,
  }
}

export function toggleChatSidebarVisibility() {
  return {
    type: types.TOGGLE_CHAT_SIDEBAR_VISIBILITY,
  }
}

export function toggleHashtagSidebarVisibility() {
  return {
    type: types.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY,
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

const addWebcastAtLocationNoCheck = (webcastId, location) => ({
  type: types.ADD_WEBCAST_AT_LOCATION,
  webcastId,
  location,
})

export function addWebcastAtLocation(webcastId, location) {
  // Before displaying the webcast, check that the provided webcast ID
  // references a webcast that actually exists
  return (dispatch, getState) => {
    if (!getState().webcastsById[webcastId]) {
      return
    }

    dispatch(addWebcastAtLocationNoCheck(webcastId, location))
  }
}

export function swapWebcasts(firstLocation, secondLocation) {
  return {
    type: types.SWAP_WEBCASTS,
    firstLocation,
    secondLocation,
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
