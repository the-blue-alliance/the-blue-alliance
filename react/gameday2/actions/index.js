import * as types from '../constants/ActionTypes'

/**
 * Takes the JSON object from the server and produces a list of normalized
 * webcasts.
 */
export function setWebcastsRaw(webcasts) {
  return {
    type: types.SET_WEBCASTS_RAW,
    webcasts
  }
}

export function toggleChatPanelVisibility() {
  return {
    type: types.TOGGLE_CHAT_PANEL_VISIBILITY
  }
}

export function toggleHashtagPanelVisibility() {
  return {
    type: types.TOGGLE_HASHTAG_PANEL_VISIBILITY
  }
}

export function addWebcast(id) {
  return {
    type: types.ADD_WEBCAST,
    id
  }
}

export function addWebcastAtLocation(webcastId, location) {
  return {
    type: types.ADD_WEBCAST_AT_LOCATION,
    webcastId,
    location
  }
}

export function removeWebcast(id) {
  return {
    type: types.REMOVE_WEBCAST,
    id
  }
}

export function resetWebcasts() {
  return {
    type: types.RESET_WEBCASTS
  }
}

export function setLayout(layoutId) {
  return {
    type: types.SET_LAYOUT,
    layoutId
  }
}
